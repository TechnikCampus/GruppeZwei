import socket
import threading
import json
import tkinter as tk
from tkinter import simpledialog, messagebox
import server


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
    def __init__(self, root, server_ip="127.0.0.1", server_port=65433):
        self.root = root
        self.root.title("Skyjo Client")
        self.network = NetworkClient(server_ip, server_port, self.handle_server_message)

        self.player_id = None
        self.grid = [["?"] * 4 for _ in range(3)]
        self.revealed = [[False] * 4 for _ in range(3)]

        self.card_buttons = [[None for _ in range(4)] for _ in range(3)]
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
                btn = tk.Button(self.root, text="?", width=6, state=tk.NORMAL,
                                command=lambda row=i, col=j: self.reveal_card(row, col))
                btn.grid(row=i, column=j, padx=5, pady=5)
                self.card_buttons[i][j] = btn

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

    def reveal_card(self, row, col):
        if not self.revealed[row][col]:
            self.network.send("reveal_card", {"row": row, "col": col})

    def handle_server_message(self, message):
        msg_type = message.get("type")
        data = message.get("data", message)

        if msg_type == "start":
            self.status_label.config(text="Spiel gestartet")
        elif msg_type == "chat":
            self.display_chat(data.get("sender", "?"), data.get("text", ""))
        elif msg_type == "reveal_result":
            row = data.get("row")
            col = data.get("col")
            card = data.get("card")
            if row is not None and col is not None:
                self.grid[row][col] = card
                self.revealed[row][col] = True
        elif msg_type == "card_drawn":
            self.status_label.config(text=f"Neue Karte gezogen: {data.get('card')}")

        self.update_gui()

    def update_gui(self):
        for i in range(3):
            for j in range(4):
                val = self.grid[i][j] if self.revealed[i][j] else "?"
                self.card_buttons[i][j].config(text=val)

    def display_chat(self, sender, message):
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f"{sender}: {message}\n")
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        ip_address = s.getsockname()[0]
    except Exception:
        ip_address = "127.0.0.1"
    finally:
        s.close()
    return ip_address


def ask_host_or_join():
    root = tk.Tk()
    root.withdraw()
    choice = messagebox.askquestion("Spiel starten", "Willst du ein Spiel hosten?")

    if choice == "yes":
        ip = get_local_ip()
        port = 65433

        def run_server():
            server.server_starten()

        threading.Thread(target=run_server, daemon=True).start()
        messagebox.showinfo("Server gestartet", f"Server läuft unter IP: {ip}\nPort: {port}")
        root.destroy()
        return ip, port

    ip = simpledialog.askstring("IP eingeben", "Gib die IP-Adresse des Hosts ein:")
    port = 65433
    root.destroy()
    return ip, port


if __name__ == "__main__":
    IP, PORT = ask_host_or_join()
    tk_root = tk.Tk()
    app = GameGUI(tk_root, server_ip=IP, server_port=PORT)
    tk_root.mainloop()
