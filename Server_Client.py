import socket
import threading
import json
import time

from SkyjoGame import SkyjoGame
from class_player import Player
from client_gui import GameGUI

PORT = 65435

spielerdaten = {}
letzte_aktion = {}
spiel_lock = threading.Lock()
SkyjoSpiel = SkyjoGame()

config = {
    "anzahl_spieler": 1,
    "anzahl_runden": 1
}

switching_cards = False
turns_left = 0
roundisOver = False
rounds = 0
finishingPlayer = None


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


def spiel_starten():
    global letzte_aktion, rounds, roundisOver, turns_left, finishingPlayer

    rounds = config["anzahl_runden"]
    roundisOver = False
    finishingPlayer = None
    turns_left = config["anzahl_spieler"]

    SkyjoSpiel.reset_game()
    SkyjoSpiel.initialize_deck()

    with spiel_lock:
        SkyjoSpiel.players.clear()
        for sid in spielerdaten:
            spieler = Player(str(sid))
            spielerdaten[sid]["spieler"] = spieler
            SkyjoSpiel.add_player(spieler)

    SkyjoSpiel.deal_initial_cards()

    for sid in spielerdaten:
        hand = spielerdaten[sid]["spieler"].hand
        spielerdaten[sid]["conn"].sendall(json.dumps({
            "type": "start",
            "player_id": sid,
            "hand": hand,
            "discard_pile": SkyjoSpiel.discard_pile
        }).encode("utf-8") + b"\n")

    letzte_aktion = {str(sid): False for sid in spielerdaten}

    SkyjoSpiel.started = True
    print("[SERVER] Spielrunde gestartet.")

    broadcast({
        "type": "turn",
        "player": SkyjoSpiel.get_current_player().id
    })


def client_thread(conn, sid):
    global switching_cards, turns_left, roundisOver, rounds, finishingPlayer, letzte_aktion
    print(f"[SERVER] Spieler {sid} verbunden.")

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

                    if typ == "join":
                        print(f"[SERVER] Spieler {sid} beigetreten als {data.get('name', 'Spieler')}.")
                        spielerdaten[sid]["name"] = data.get("name", f"Spieler{sid}")
                        if len(spielerdaten) == config["anzahl_spieler"]:
                            threading.Thread(target=spiel_starten, daemon=True).start()

                    elif typ == "reveal_card":
                        current_player = SkyjoSpiel.get_current_player()

                        if current_player is None or current_player.id != str(sid):
                            continue

                        if letzte_aktion.get(str(sid), False):
                            continue

                        index = data["data"].get("index", 0)
                        i = index // 4
                        j = index % 4
                        spieler = spielerdaten[sid]["spieler"]

                        if switching_cards:
                            switching_cards = False
                            temp = spieler.hand[index]
                            spieler.hand[index] = SkyjoSpiel.discard_pile.pop()
                            SkyjoSpiel.discard_pile.append(temp)

                            broadcast({"type": "deck_drawn_card", "card": temp})

                            if not spieler.is_card_revealed(i, j):
                                spieler.reveal_card(i, j)

                            conn.sendall(json.dumps({
                                "type": "deck_switched_card",
                                "hand": spieler.hand,
                                "index": index
                            }).encode("utf-8") + b"\n")
                        else:
                            if not spieler.is_card_revealed(i, j):
                                spieler.reveal_card(i, j)

                            letzte_aktion[str(sid)] = True
                            broadcast({
                                "type": "reveal_result",
                                "data": {"index": i * 4 + j},
                                "player": sid
                            })

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

                    elif typ == "discard_pile_draw":
                        switching_cards = True

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

                    elif typ == "chat":
                        broadcast({
                            "type": "chat",
                            "sender": spielerdaten[sid]["name"],
                            "text": data.get("text", "")
                        })

                    elif typ == "round_over":
                        spieler = data.get("player", "?")
                        print(f"{spieler} hat die Runde beendet")

                        if not roundisOver:
                            roundisOver = True
                            finishingPlayer = spieler
                            turns_left = len(spielerdaten) - 1
                            rounds -= 1
                        else:
                            turns_left -= 1

                        if turns_left <= 0:
                            if rounds <= 0:
                                broadcast({"type": "game_over"})
                                time.sleep(5)
                                with spiel_lock:
                                    spielerdaten.clear()
                                roundisOver = False
                                turns_left = 0
                                rounds = 0
                                return
                            else:
                                print("[SERVER] Neue Runde beginnt.")
                                SkyjoSpiel.reset_game()
                                SkyjoSpiel.initialize_deck()
                                SkyjoSpiel.players.clear()
                                for sid in spielerdaten:
                                    spieler = Player(str(sid))
                                    spielerdaten[sid]["spieler"] = spieler
                                    SkyjoSpiel.add_player(spieler)
                                SkyjoSpiel.deal_initial_cards()
                                nextPlayer = SkyjoSpiel.get_current_player().id
                                for sid in spielerdaten:
                                    hand = spielerdaten[sid]["spieler"].hand
                                    spielerdaten[sid]["conn"].sendall(json.dumps({
                                        "type": "new_round",
                                        "player_id": sid,
                                        "hand": hand,
                                        "discard_pile": SkyjoSpiel.discard_pile
                                    }).encode("utf-8") + b"\n")
                                roundisOver = False
                                finishingPlayer = None
                                letzte_aktion = {str(sid): True for sid in spielerdaten}
                                letzte_aktion[str(nextPlayer)] = False
                                broadcast({
                                    "type": "turn",
                                    "player": str(nextPlayer),
                                    "name": spielerdaten[int(nextPlayer)]["name"]
                                })

                except json.JSONDecodeError:
                    print("[SERVER] Ungültige Nachricht erhalten.")
    except:
        print(f"[SERVER] Spieler {sid} getrennt.")
    finally:
        with spiel_lock:
            if sid in spielerdaten:
                del spielerdaten[sid]
        conn.close()


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
