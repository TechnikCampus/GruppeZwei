# ==== Module & Abhängigkeiten ====
import socket
import threading
import json
from SkyjoGame import SkyjoGame  # Spiellogik
from class_player import Player  # Spielerklasse
from networkClientClass import NetworkClient  # Netzwerk-Client (Client-Seite)
import time
from KeyboardInputHandler_class import KeyboardInputHandler
from GameGUI_class import GameGUI

# ==== Konfiguration & Spielstatus ====
PORT = 65435  # Port des Servers

spielerdaten = {}  # Speichert zu jedem Spieler: Verbindung, Name, Spielerobjekt
letzte_aktion = {}  # Merkt sich, ob Spieler in dieser Runde schon etwas getan hat
spiel_lock = threading.Lock()  # Für Thread-Synchronisation
SkyjoSpiel = SkyjoGame()  # Initialisiere das Skyjo-Spielobjekt

config = {
    "anzahl_spieler": 1,  # Anzahl der Spieler
    "anzahl_runden": 1    # Anzahl der Spielrunden
}

switching_cards = False  # Wird true, wenn ein Spieler eine Karte tauscht
turns_left = 0  # Wie viele Spieler müssen noch handeln nach Rundenschluss?
roundisOver = False  # Ob die aktuelle Runde beendet wurde
rounds = 0  # Anzahl verbleibender Runden
finishingPlayer = 9  # Spieler, der die Runde beendet hat


# ==== Nachricht an alle Clients senden ====
def broadcast(message, exclude=None):
    raw = json.dumps(message).encode("utf-8") + b"\n"
    with spiel_lock:
        for sid, daten in spielerdaten.items():
            if exclude is not None and sid == exclude:
                continue
            try:
                daten["conn"].sendall(raw)
            except:
                continue


# ==== Spielrunde starten ====
def spiel_starten():
    global letzte_aktion

    for runde in range(config["anzahl_runden"]):
        SkyjoSpiel.reset_game()
        SkyjoSpiel.initialize_deck()

        with spiel_lock:
            SkyjoSpiel.players.clear()
            for sid in spielerdaten:
                spieler = Player(str(sid))  # Spielerobjekt erzeugen
                spielerdaten[sid]["spieler"] = spieler
                SkyjoSpiel.add_player(spieler)  # Spieler dem Spiel hinzufügen

        SkyjoSpiel.deal_initial_cards()  # Karten verteilen

        # Starte das Spiel für jeden Spieler
        for sid in spielerdaten:
            hand = spielerdaten[sid]["spieler"].hand
            spielerdaten[sid]["conn"].sendall(json.dumps({
                "type": "start",
                "player_id": sid,
                "hand": hand,
                "discard_pile": SkyjoSpiel.discard_pile,
            }).encode("utf-8") + b"\n")

        letzte_aktion = {str(sid): False for sid in spielerdaten}  # Reset Aktionstracker
        for k in list(letzte_aktion.keys()):
            if isinstance(k, int):
                del letzte_aktion[k]

        SkyjoSpiel.started = True
        print("[SERVER] Spielrunde gestartet.")

        # Der erste Spieler ist am Zug
        broadcast({
            "type": "turn",
            "player": SkyjoSpiel.get_current_player().id
        })


# ==== Server-Thread für jeden Client ====
def client_thread(conn, sid):
    global switching_cards, turns_left, roundisOver, rounds, finishingPlayer
    print(f"[SERVER] Spieler {sid} verbunden.")
    turns_left = config["anzahl_spieler"]

    buffer = b""
    try:
        while True:
            chunk = conn.recv(4096)
            if not chunk:
                break
            buffer += chunk
            while b"\n" in buffer:
                raw, buffer = buffer.split(b"\n", 1)
                try:
                    daten = json.loads(raw.decode("utf-8"))
                    typ = daten.get("type")
                    data = daten.get("data", {})

                    # ==== Spieler tritt bei ====
                    if typ == "join":
                        print(f"[SERVER] Spieler {sid} beigetreten als {data.get('name', 'Spieler')}.")
                        spielerdaten[sid]["name"] = data.get("name", f"Spieler{sid}")
                        if len(spielerdaten) == config["anzahl_spieler"]:
                            threading.Thread(target=spiel_starten, daemon=True).start()

                    # ==== Karte aufdecken ====
                    elif (typ == "reveal_card"):
                        current_player = SkyjoSpiel.get_current_player().id

                        endRound()

                        if current_player is None or current_player != str(sid):
                           print(f"[SERVER] Spieler {sid} ist NICHT am Zug – Aktion ignoriert.")
                           continue

                        # Spieler hat bereits aufgedeckt
                        if letzte_aktion.get(str(sid), False):
                            print(f"[SERVER] Spieler {sid} hat in diesem Zug bereits eine Karte aufgedeckt.")
                            continue

                        index = data["data"].get("index", 0)
                        i = index // 4
                        j = index % 4
                        spieler = spielerdaten[sid]["spieler"]

                        # ==== Karten tauschen ====
                        if switching_cards:
                            switching_cards = False
                            temp = spieler.hand[index]
                            spieler.hand[index] = SkyjoSpiel.discard_pile.pop()
                            SkyjoSpiel.discard_pile.append(temp)

                            broadcast({
                                "type": "deck_drawn_card",
                                "card": temp
                            })

                            if not spieler.is_card_revealed(i, j):
                                wert = spieler.reveal_card(i, j)

                            conn.sendall(json.dumps({
                                "type": "deck_switched_card",
                                "hand": spieler.hand,
                                "index": index
                            }).encode("utf-8") + b"\n")

                            print(f"[DEGUGG] Index: {index}")

                            SkyjoSpiel.next_turn()
                            next_id = SkyjoSpiel.get_current_player().id
                            for k in letzte_aktion:
                                letzte_aktion[k] = True
                            letzte_aktion[str(next_id)] = False

                            broadcast({
                                "type": "turn",
                                "player": str(next_id),
                                "name": spielerdaten[sid]["name"]
                            })

                            # Dreierprüfung in Spalten
                            for i in range(4):
                                idx1 = i
                                idx2 = i + 4
                                idx3 = i + 8
                                if (
                                    spieler.hand[idx1] == spieler.hand[idx2] == spieler.hand[idx3] and spieler.hand[idx1] != 13
                                ):
                                    print(f"Dreier gefunden in Spalte {i}")

                                    SkyjoSpiel.discard_pile.append(spieler.hand[idx1])
                                    SkyjoSpiel.discard_pile.append(spieler.hand[idx2])
                                    SkyjoSpiel.discard_pile.append(spieler.hand[idx3])

                                    temp = spieler.hand[idx1]

                                    spieler.hand[idx1] = 13
                                    spieler.hand[idx2] = 13
                                    spieler.hand[idx3] = 13

                                    conn.sendall(json.dumps({
                                        "type": "threesome",
                                        "hand": spieler.hand
                                    }).encode("utf-8") + b"\n")

                                    conn.sendall(json.dumps({
                                        "type": "deck_drawn_card",
                                        "card": temp
                                    }).encode("utf-8") + b"\n")

                        # ==== Karte einfach aufdecken ====
                        else:
                            if not spieler.is_card_revealed(i, j):
                                wert = spieler.reveal_card(i, j)
                                print(f"[SERVER] Spieler {sid} deckt Karte {i},{j} = {wert} auf")

                                letzte_aktion[str(sid)] = True

                                broadcast({
                                    "type": "reveal_result",
                                    "data": {"index": i * 4 + j},
                                    "player": sid
                                })

                                SkyjoSpiel.next_turn()
                                next_id = SkyjoSpiel.get_current_player().id
                                print(f"[DEBUG] Nächster Spieler ist: {next_id}")
                                for k in letzte_aktion:
                                    letzte_aktion[k] = True
                                letzte_aktion[str(next_id)] = False
                                print(f"[DEBUG] letzte_aktion nach Spielerwechsel: {letzte_aktion}")
                                broadcast({
                                    "type": "turn",
                                    "player": str(next_id),
                                    "name": spielerdaten[sid]["name"]
                                })

                            # Dreierprüfung erneut
                            for i in range(4):
                                idx1 = i
                                idx2 = i + 4
                                idx3 = i + 8
                                if (
                                    spieler.hand[idx1] == spieler.hand[idx2] == spieler.hand[idx3] and spieler.hand[idx1] != 13
                                ):
                                    print(f"Dreier gefunden in Spalte {i}")

                                    SkyjoSpiel.discard_pile.append(spieler.hand[idx1])
                                    SkyjoSpiel.discard_pile.append(spieler.hand[idx2])
                                    SkyjoSpiel.discard_pile.append(spieler.hand[idx3])

                                    temp = spieler.hand[idx1]

                                    spieler.hand[idx1] = 13
                                    spieler.hand[idx2] = 13
                                    spieler.hand[idx3] = 13

                                    conn.sendall(json.dumps({
                                        "type": "threesome",
                                        "hand": spieler.hand
                                    }).encode("utf-8") + b"\n")

                                    conn.sendall(json.dumps({
                                        "type": "deck_drawn_card",
                                        "card": temp
                                    }).encode("utf-8") + b"\n")

                    # ==== Chatnachricht senden ====
                    elif typ == "chat":
                        broadcast({
                            "type": "chat",
                            "sender": spielerdaten[sid]["name"],
                            "text": data.get("text", "")
                        })

                    # ==== Karte vom Deck ziehen ====
                    elif typ == "deck_draw_card":
                        neue_karte = SkyjoSpiel.draw_new_card() if SkyjoSpiel.deck else None
                        if neue_karte:
                            SkyjoSpiel.discard_pile.append(neue_karte)
                            conn.sendall(json.dumps({
                                "type": "deck_drawn_card",
                                "card": neue_karte
                            }).encode("utf-8") + b"\n")
                            broadcast({
                                "type": "deck_update",
                                "deck_count": len(SkyjoSpiel.deck),
                                "card": neue_karte
                            })

                    # ==== Karte vom Ablagestapel ziehen (für Tausch) ====
                    elif typ == "discard_pile_draw":
                        switching_cards = True

                    # ==== Spieler beendet Runde ====
                    elif typ == "round_over":
                        spieler = data.get("player", "?")
                        print(f"{spieler} hat die Runde beendet")
                        turns_left -= 1
                        if roundisOver is not True:
                            rounds -= 1
                        roundisOver = True
                        if finishingPlayer == 9:
                            finishingPlayer = spieler
                        
                        if turns_left <= 0:
                            roundisOver = True
                            endRound()

                    elif typ == "100P":
                        # Spiel vorbei
                        spieler = data.get("player", "?")
                        broadcast({
                            "type": "100Pointz", 
                            "player": spieler
                        })
                        time.sleep(5)
                        with spiel_lock:
                            spielerdaten.clear()
                        roundisOver = False
                        turns_left = 0
                        rounds = 0


                except json.JSONDecodeError:
                    print("[SERVER] Ungültige Nachricht erhalten.")
    except:
        print(f"[SERVER] Spieler {sid} getrennt.")
    finally:
        with spiel_lock:
            if sid in spielerdaten:
                del spielerdaten[sid]
        conn.close()


# ==== Serverstart ====
def server_starten(konfig):
    global config, turns_left, rounds
    config = konfig

    turns_left = config["anzahl_spieler"]
    rounds = config["anzahl_runden"]

    SkyjoSpiel.reset_game()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", PORT))
    server.listen(10)
    print(f"[SERVER] Skyjo-Server gestartet auf Port {PORT}")

    sid = 0
    while True:
        conn, addr = server.accept()
        with spiel_lock:
            if len(spielerdaten) >= config["anzahl_spieler"]:
                conn.close()
                continue
            spielerdaten[sid] = {"conn": conn}
        threading.Thread(target=client_thread, args=(conn, sid), daemon=True).start()
        sid += 1

def endRound():
    global roundisOver, turns_left, rounds
    if turns_left <= 0:
        if rounds <= 0:
            try:
                # Calculate final scores
                final_scores = {}
                for sid, data in spielerdaten.items():
                    player_name = f"Spieler {sid} als {data['name']}"
                    player = data["spieler"]
                    
                    # Sum up all card values in the grid
                    score = 0
                    for i in range(len(player.grid)):
                        for j in range(len(player.grid[i])):
                            value = player.grid[i][j]
                            if value is not None:  # Only count revealed cards
                                score += value
                    
                    final_scores[player_name] = score
                    print(f"[DEBUG] Final score for {player_name}: {score}")
                
                print(f"[DEBUG] Final scores before sorting: {final_scores}")
                
                # Send scores to clients
                broadcast({
                    "type": "game_over",
                    "final_scores": final_scores
                })
                
            except Exception as e:
                print(f"[ERROR] Error during game end: {e}")

def bubble_sort_scores(scores_dict):
    """
    Sortiert die Spieler nach Punktzahl (aufsteigend)
    
    Args:
        scores_dict: Dictionary mit Spielernamen und Punkten
    Returns:
        Liste von Tupeln (name, score), aufsteigend sortiert
    """
    items = list(scores_dict.items())
    n = len(items)
    
    for i in range(n):
        for j in range(0, n - i - 1):
            if items[j][1] > items[j + 1][1]:
                items[j], items[j + 1] = items[j + 1], items[j]
    
    return items

class SkyjoGame:
    def __init__(self):
        self.final_scores = {}  # Neue Variable für finale Punktestände
    
    def handle_submit_score(self, player_id, data):
        """Handle submitted score from client"""
        score = data.get("score", 0)
        name = data.get("name", f"Player {player_id}")
        player_key = f"Spieler {player_id} als {name}"
        
        print(f"[DEBUG] Received score from {player_key}: {score}")
        self.final_scores[player_key] = score
        
        # Check if all scores are in
        if len(self.final_scores) == len(self.spielerdaten):
            print(f"[DEBUG] All scores received: {self.final_scores}")
            self.broadcast_final_scores()

    def broadcast_final_scores(self):
        """Send final scores to all clients"""
        print(f"[DEBUG] Broadcasting final scores: {self.final_scores}")
        self.broadcast({
            "type": "game_over",
            "final_scores": self.final_scores
        })
