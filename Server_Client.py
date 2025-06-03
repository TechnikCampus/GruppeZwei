import socket
import threading
import json
import random
import tkinter as tk
from tkinter import simpledialog
import sys

# ==== Gemeinsame Parameter ====
PORT = 65435
MAX_SPIELER = 4
KARTEN_PRO_SPIELER = 12
KARTEN_DECK = [-2] * 5 + list(range(0, 13)) * 10
random.shuffle(KARTEN_DECK)

spielerdaten = {}
spiel_lock = threading.Lock()

# ==== Server-Funktionen ====
def karten_ziehen(anzahl):
    return [KARTEN_DECK.pop() for _ in range(anzahl) if KARTEN_DECK]cli

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

def client_thread(conn, sid):
    print(f"Spieler {sid} verbunden.")
    karten = karten_ziehen(KARTEN_PRO_SPIELER)
    with spiel_lock:
        spielerdaten[sid]["karten"] = karten

    conn.sendall(json.dumps({
        "type": "start",
        "player_id": sid,
        "hand": karten
    }).encode("utf-8") + b"\n")

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
                    if typ == "join":
                        print(f"{daten['data'].get('name', 'Unbekannt')} ist dem Spiel beigetreten.")
                    elif typ == "chat":
                        broadcast({
                            "type": "chat",
                            "sender": daten["data"].get("sender", "?"),
                            "text": daten["data"].get("text", "")
                        })
                    elif typ == "draw_card":
                        neue_karte = karten_ziehen(1)[0] if KARTEN_DECK else None
                        spielerdaten[sid]["karten"].append(neue_karte)
                        conn.sendall(json.dumps({
                            "type": "card_drawn",
                            "card": neue_karte
                        }).encode("utf-8") + b"\n")
                    elif typ == "reveal_card":
                        broadcast({
                            "type": "reveal_result",
                            "data": daten["data"],
                            "player": sid
                        })
                except json.JSONDecodeError:
                    print("Ungültige Nachricht")
    except:
        print(f"Spieler {sid} getrennt.")
    finally:
        with spiel_lock:
            if sid in spielerdaten:
                del spielerdaten[sid]
        conn.close()

def server_starten():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", PORT))
    server.listen(MAX_SPIELER)
    print(f"Skyjo-Server läuft auf Port {PORT}")

    sid = 0
    while sid < MAX_SPIELER:
        conn, addr = server.accept()
        with spiel_lock:
            spielerdaten[sid] = {"conn": conn, "karten": []}
        threading.Thread(target=client_thread, args=(conn, sid), daemon=True).start()
        sid += 1

# ==== Client-Funktionen ====
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

class GameGUI:
    def __init__(self, root, server_ip, server_port):
        self.root = root
        self.root.title("Skyjo Client")

        self.player_id = None
        self.hand = ["?"] * 12
        self.revealed = [False] * 12

        self.card_buttons = []
        self.chat_entry = tk.Entry(root, width=40)
        self.chat_button = tk.Button(root, text="Senden", command=self.send_chat_message)
        self.chat_display = tk.Text(root, height=10, width=60, state=tk.DISABLED)
        self.status_label = tk.Label(root, text="Status")
        self.build_gui()

        self.prompt_player_name()
        self.network = NetworkClient(server_ip, server_port, self.handle_server_message, self.on_connected)
        self.root.after(100, self.connect_to_server)

    def build_gui(self):
        for i in range(3):
            for j in range(4):
                idx = i * 4 + j
                btn = tk.Button(self.root, text="?", width=6, state=tk.NORMAL,
                                command=lambda idx=idx: self.reveal_card(idx))
                btn.grid(row=i, column=j, padx=5, pady=5)
                self.card_buttons.append(btn)

        self.status_label.grid(row=3, column=0, columnspan=4)
        self.chat_display.grid(row=4, column=0, columnspan=4)
        self.chat_entry.grid(row=5, column=0, columnspan=3)
        self.chat_button.grid(row=5, column=3)

    def prompt_player_name(self):
        name = None
        while not name:
            name = simpledialog.askstring("Spielername", "Gib deinen Spielernamen ein:")
        self.player_id = name

    def connect_to_server(self):
        connected = self.network.connect()
        if not connected:
            self.status_label.config(text="Verbindung fehlgeschlagen")

    def on_connected(self):
        self.status_label.config(text="Verbunden mit Server")
        self.network.send("join", {"name": self.player_id})

    def send_chat_message(self):
        text = self.chat_entry.get().strip()
        if text:
            self.network.send("chat", {"text": text, "sender": self.player_id})
            self.chat_entry.delete(0, tk.END)

    def reveal_card(self, idx):
        self.revealed[idx] = True
        self.update_gui()
        self.network.send("reveal_card", {"data": {"index": idx}})

    def handle_server_message(self, message):
        msg_type = message.get("type")
        data = message.get("data", message)

        if msg_type == "start":
            self.hand = data.get("hand", self.hand)
            self.status_label.config(text="Spiel gestartet")
        elif msg_type == "chat":
            self.display_chat(data.get("sender", "?"), data.get("text", ""))
        elif msg_type == "reveal_result":
            idx = data.get("data", {}).get("index")
            if idx is not None:
                self.revealed[idx] = True
        elif msg_type == "card_drawn":
            card = data.get("card")
            if card is not None:
                self.hand.append(card)

        self.update_gui()

    def update_gui(self):
        for i, btn in enumerate(self.card_buttons):
            val = self.hand[i] if self.revealed[i] else "?"
            btn.config(text=val)

    def display_chat(self, sender, message):
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f"{sender}: {message}\n")
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)

# ==== Einstiegspunkt ====
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()

    modus = simpledialog.askstring("Modus", "Host oder Client?")
    if modus is None:
        sys.exit(0)

    modus = modus.lower()

    if modus == "host":
        threading.Thread(target=server_starten, daemon=True).start()
        root.deiconify()
        app = GameGUI(root, "localhost", PORT)
        root.mainloop()
    elif modus == "client":
        ip = simpledialog.askstring("IP-Adresse", "IP des Hosts eingeben:")
        if ip:
            root.deiconify()
            app = GameGUI(root, ip, PORT)
            root.mainloop()
