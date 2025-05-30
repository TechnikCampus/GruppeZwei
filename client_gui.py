import tkinter as tk
from tkinter import messagebox, simpledialog
from client_network import NetworkClient
from class_player import Player
from keyboard_input import KeyboardInputHandler
import threading
import time

class GameGUI:
    def __init__(self, root, server_ip="127.0.0.1", server_port=65433):
        self.root = root
        self.root.title("Skyjo Client")
        self.network = NetworkClient(server_ip, server_port, self.handle_server_message)

        self.player = None
        self.current_player = None

        self.card_buttons = [[None for _ in range(4)] for _ in range(3)]
        self.chat_entry = tk.Entry(root, width=40)
        self.chat_button = tk.Button(root, text="Senden", command=self.send_chat_message)
        self.chat_display = tk.Text(root, height=10, width=60, state=tk.DISABLED)
        self.status_label = tk.Label(root, text="Status")

        self.timer_label = tk.Label(root, text="Zug-Timer: -")
        self.timer_active = False

        self.build_gui()
        self.prompt_player_name()
        self.keyboard = KeyboardInputHandler(self.root, self.network, self.card_buttons)
        self.root.after(100, self.connect_to_server)

    def build_gui(self):
        for i in range(3):
            for j in range(4):
                btn = tk.Button(self.root, text="?", width=6, state=tk.DISABLED)
                btn.grid(row=i, column=j, padx=5, pady=5)
                self.card_buttons[i][j] = btn

        self.timer_label.grid(row=3, column=0, columnspan=2)
        self.status_label.grid(row=3, column=2, columnspan=2)

        chat_frame = tk.Frame(self.root)
        chat_frame.grid(row=4, column=0, columnspan=4)
        self.chat_display.pack(in_=chat_frame)
        self.chat_entry.pack(in_=chat_frame, side=tk.LEFT)
        self.chat_button.pack(in_=chat_frame, side=tk.RIGHT)

        self.root.bind("<Return>", lambda e: self.send_chat_message())
        self.root.bind("<Escape>", lambda e: self.root.quit())

    def prompt_player_name(self):
        name = None
        while not name:
            name = simpledialog.askstring("Spielername", "Gib deinen Spielernamen ein:")
        self.player = Player(name)
        self.root.title(f"Skyjo – {self.player.id}")

    def connect_to_server(self):
        connected = self.network.connect()
        if connected:
            self.network.send("join", {"name": self.player.id})
        else:
            self.status_label.config(text="Verbindung fehlgeschlagen")

    def send_chat_message(self):
        text = self.chat_entry.get().strip()
        if text:
            self.network.send("chat", {"text": text, "sender": self.player.id})
            self.chat_entry.delete(0, tk.END)

    def handle_server_message(self, message):
        msg_type = message.get("type")
        data = message.get("data", message)

        if msg_type == "start":
            self.player.hand = data.get("hand", [])
            self.display_chat("System", f"Spieler {data.get('player_id')} verbunden.")
        elif msg_type == "card_drawn":
            card = data.get("card")
            if card is not None:
                self.player.hand.append(card)
                self.display_chat("System", f"Du hast eine Karte gezogen: {card}")
        elif msg_type == "game_state":
            self.display_chat("System", data.get("info", "Spielstatus empfangen."))
        elif msg_type == "reveal_result":
            pos = data.get("data", {})
            row, col = pos.get("row"), pos.get("col")
            if row is not None and col is not None:
                self.player.revealed[row][col] = True
                self.player.grid[row][col] = "X"
        elif msg_type == "chat":
            sender = data.get("sender", "?")
            text = data.get("text", "")
            self.display_chat(sender, text)

        self.update_gui()

    def update_gui(self):
        for i in range(3):
            for j in range(4):
                val = self.player.grid[i][j] if self.player.revealed[i][j] else "?"
                self.card_buttons[i][j].config(text=val)

        if self.current_player == self.player.id:
            self.status_label.config(text="Du bist am Zug")
            self.start_timer()
        else:
            self.status_label.config(text=f"Warte auf {self.current_player}...")

    def display_chat(self, sender, message):
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f"{sender}: {message}\n")
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)

    def start_timer(self, duration=30):
        self.timer_active = True

        def count():
            for t in range(duration, 0, -1):
                if not self.timer_active:
                    break
                self.timer_label.config(text=f"Zug-Timer: {t}s")
                time.sleep(1)
            if self.timer_active:
                self.timer_label.config(text="Zeit abgelaufen!")

        threading.Thread(target=count, daemon=True).start()

if __name__ == '__main__':
    root = tk.Tk()
    app = GameGUI(root)
    root.mainloop()
