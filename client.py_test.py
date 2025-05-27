# client.py
import socket
import threading
import json
import tkinter as tk
from tkinter import simpledialog

class NetworkClient:
    def __init__(self, server_ip, server_port, on_message):
        self.server_ip = server_ip
        self.server_port = server_port
        self.on_message = on_message
        self.sock = None
        self.running = False
        self.buffer = b""

    def connect(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.server_ip, self.server_port))
            self.running = True
            threading.Thread(target=self._receive_loop, daemon=True).start()
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
    def __init__(self, root, server_ip="10.148.101.74", server_port=65433):
        self.root = root
        self.root.title("Skyjo Client")
        self.network = NetworkClient(server_ip, server_port, self.handle_server_message)

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
        self.root.after(100, self.connect_to_server)

    def build_gui(self):
        for i in range(3):
            for j in range(4):
                idx = i * 4 + j
                btn = tk.Button(self.root, text="?", width=6, state=tk.DISABLED,
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
        if connected:
            self.network.send("join", {"name": self.player_id})
        else:
            self.status_label.config(text="Verbindung fehlgeschlagen")

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

if __name__ == "__main__":
    root = tk.Tk()
    app = GameGUI(root)
    root.mainloop()
