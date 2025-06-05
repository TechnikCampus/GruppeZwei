import socket
import threading
import json
# import random

from SkyjoGame import SkyjoGame
from class_player import Player

# ==== Konfiguration & Spielstatus ====
PORT = 65435


class NetworkClient:
    def __init__(self, server_ip, server_port, on_message, on_connected=None):
        self.server_ip = server_ip
        self.server_port = server_port
        self.on_message = on_message
        self.on_connected = on_connected
        self.sock = None
        self.running = False
        self.buffer = b""

    def connect(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.server_ip, self.server_port))
            self.running = True
            threading.Thread(target=self._receive_loop, daemon=True).start()
            if self.on_connected:
                self.on_connected()
            return True
        except Exception as e:
            print(f"[ERROR] Verbindung fehlgeschlagen: {e}")
            return False

    def send(self, msg_type, data=None):
        if not self.running:
            print("[WARN] Nicht verbunden mit Server")
            return
        message = json.dumps({"type": msg_type, "data": data or {}}).encode("utf-8") + b"\n"
        try:
            self.sock.sendall(message)
        except Exception as e:
            print(f"[ERROR] Sendefehler: {e}")

    def _receive_loop(self):
        while self.running:
            try:
                chunk = self.sock.recv(4096)
                if not chunk:
                    break
                self.buffer += chunk
                while b"\n" in self.buffer:
                    raw, self.buffer = self.buffer.split(b"\n", 1)
                    try:
                        msg = json.loads(raw.decode("utf-8"))
                        self.on_message(msg)
                    except json.JSONDecodeError:
                        print("[WARN] Ungültige Nachricht erhalten.")
            except Exception as e:
                print(f"[ERROR] Empfangsfehler: {e}")
                break


spielerdaten = {}
letzte_aktion = {}
spiel_lock = threading.Lock()
SkyjoSpiel = SkyjoGame()

config = {
    "anzahl_spieler": 2,
    "anzahl_runden": 1
}


# ==== Netzwerkfunktionen ====
def karten_ziehen(anzahl):
    return SkyjoSpiel.draw_cards(anzahl)


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


# ==== Spiellogik ====
def spiel_starten():
    global letzte_aktion

    for runde in range(config["anzahl_runden"]):
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
                "hand": hand
            }).encode("utf-8") + b"\n")
        
        letzte_aktion = {str(sid): False for sid in spielerdaten} # Reset letzte Aktion für alle Spieler
        # Entferne alle int-Keys, falls noch vorhanden
        for k in list(letzte_aktion.keys()):
            if isinstance(k, int):
                del letzte_aktion[k]

        SkyjoSpiel.started = True
        print("[SERVER] Spielrunde gestartet.")

        # Ersten Spieler benachrichtigen
        broadcast({
            "type": "turn",
            "player": SkyjoSpiel.get_current_player().id
        })



# ==== Server-Thread pro Client ====
def client_thread(conn, sid):
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
                        print(f"[DEBUG] Aktueller Spieler laut Server: {current_player.id if current_player else 'None'} | Aktuell anfragender: {sid}")
                        print(f"[DEBUG] letzte_aktion vor Prüfung: {letzte_aktion}")
                        if current_player is None or current_player.id != str(sid):
                            print(f"[SERVER] Spieler {sid} ist NICHT am Zug – Aktion ignoriert.")
                            continue

                        # Nur eine Aktion pro Zug erlauben
                        if letzte_aktion.get(str(sid), False):
                            print(f"[SERVER] Spieler {sid} hat in diesem Zug bereits eine Karte aufgedeckt.")
                            continue

                        index = data["data"].get("index", 0)
                        i = index // 4
                        j = index % 4

                        spieler = spielerdaten[sid]["spieler"]

                        if not spieler.is_card_revealed(i, j):
                            wert = spieler.reveal_card(i, j)
                            print(f"[SERVER] Spieler {sid} deckt Karte {i},{j} = {wert} auf")

                            # Merke: Spieler hat in diesem Zug bereits gehandelt
                            letzte_aktion[str(sid)] = True
                            print(f"[DEBUG] letzte_aktion nach Aufdecken: {letzte_aktion}")

                            # Nachricht an alle Clients
                            broadcast({
                                "type": "reveal_result",
                                "data": {"index": i * 4 + j},
                                "player": sid
                            })

                            if SkyjoSpiel.check_for_end(spieler):
                                print(f"[SERVER] Spieler {sid} hat alle Karten aufgedeckt – Spielende.")
                                broadcast({
                                    "type": "game_over",
                                    "winner": sid
                                })
                            else:
                                SkyjoSpiel.next_turn()
                                next_id = SkyjoSpiel.get_current_player().id
                                print(f"[DEBUG] Nächster Spieler ist: {next_id}")
                                for k in letzte_aktion:
                                    letzte_aktion[k] = True
                                letzte_aktion[str(next_id)] = False
                                print(f"[DEBUG] letzte_aktion nach Spielerwechsel: {letzte_aktion}")
                                broadcast({
                                    "type": "turn",
                                    "player": str(next_id)
                                })

                    elif typ == "chat":
                        broadcast({
                            "type": "chat",
                            "sender": spielerdaten[sid]["name"],
                            "text": data.get("text", "")
                        })

                    elif typ == "draw_card":
                        neue_karte = karten_ziehen(1)[0] if SkyjoSpiel.deck else None
                        if neue_karte:
                            spielerdaten[sid]["spieler"].hand.append(neue_karte)
                            conn.sendall(json.dumps({
                                "type": "card_drawn",
                                "card": neue_karte
                            }).encode("utf-8") + b"\n")
                            broadcast({
                                "type": "deck_update",
                                "deck_count": len(SkyjoSpiel.deck)
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


# ==== Haupt-Serverfunktion ====
def server_starten(konfig):
    print("[DEBUG] server_starten() wurde aufgerufen")
    global config
    config = konfig

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
