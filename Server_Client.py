import socket
import threading
import json
import random

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
    for runde in range(config["anzahl_runden"]):
        SkyjoSpiel.reset_game()
        SkyjoSpiel.initialize_deck()

        with spiel_lock:
            SkyjoSpiel.players.clear()
            for sid in spielerdaten:
                spieler = Player(str(sid))
                SkyjoSpiel.add_player(spieler)
                spielerdaten[sid]["spieler"] = spieler

        SkyjoSpiel.deal_initial_cards()

        for sid in spielerdaten:
            hand = spielerdaten[sid]["spieler"].hand
            spielerdaten[sid]["conn"].sendall(json.dumps({
                "type": "start",
                "player_id": sid,
                "hand": hand
            }).encode("utf-8") + b"\n")

        SkyjoSpiel.started = True
        print("[SERVER] Spielrunde gestartet.")

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

                        if len(spielerdaten) == config["anzahl_spieler"]:
                            threading.Thread(target=spiel_starten, daemon=True).start()

                    elif typ == "reveal_card":
                        i = data["data"].get("index", 0) // 4
                        j = data["data"].get("index", 0) % 4
                        spieler = spielerdaten[sid]["spieler"]
                        if not spieler.is_card_revealed(i, j):
                            wert = spieler.reveal_card(i, j)
                            print(f"[SERVER] Spieler {sid} deckt Karte {i},{j} = {wert} auf")
                            broadcast({
                                "type": "reveal_result",
                                "data": {"index": i * 4 + j},
                                "player": sid
                            })

                    elif typ == "chat":
                        broadcast({
                            "type": "chat",
                            "sender": data.get("sender", f"Spieler{sid}"),
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

