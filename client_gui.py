import tkinter as tk
from tkinter import simpledialog
from Server_Client import NetworkClient

PORT = 65435


class GameGUI:
    def __init__(self, root, server_ip, server_port):
        self.root = root
        self.root.title("Skyjo Client")

        self.player_id = None
        self.hand = ["?"] * 12
        self.revealed = [False] * 12
        self.is_my_turn = False  # Flag: bin ich am Zug?

        self.card_buttons = []
        self.chat_entry = tk.Entry(root, width=40)
        self.chat_button = tk.Button(root, text="Senden", command=self.send_chat_message)
        self.chat_display = tk.Text(root, height=10, width=60, state=tk.DISABLED)
        self.status_label = tk.Label(root, text="Status")
        self.deck_label = tk.Label(self.root, text="Stapel: ? Karten")
        self.deck_label.grid(row=6, column=0, columnspan=2)
        self.build_gui()

        self.prompt_player_name()
        self.network = NetworkClient(server_ip, server_port, self.handle_server_message, self.on_connected)
        self.root.after(100, self.connect_to_server)

    def build_gui(self):
        for i in range(3):
            for j in range(4):
                idx = i * 4 + j
                btn = tk.Button(self.root, text="?", width=6, state=tk.DISABLED,
                                command=lambda idx=idx: self.reveal_card(idx))
                btn.grid(row=i, column=j, padx=5, pady=5)
                self.card_buttons.append(btn)

        self.deck_label.grid(row=1, column=4, rowspan=2, padx=10, pady=10, sticky="n")

        self.status_label.grid(row=3, column=0, columnspan=4)
        self.chat_display.grid(row=4, column=0, columnspan=4)
        self.chat_entry.grid(row=5, column=0, columnspan=3)
        self.chat_button.grid(row=5, column=3)

    def prompt_player_name(self):
        name = None
        while not name:
            name = simpledialog.askstring("Spielername", "Gib deinen Spielernamen ein:")
        self.player_id = str(name)
        print(f"[DEBUG] Spielername gesetzt: {self.player_id}")

    def connect_to_server(self):
        connected = self.network.connect()
        if not connected:
            self.status_label.config(text="Verbindung fehlgeschlagen")

    def on_connected(self):
        self.status_label.config(text="Verbunden mit Server")
        print(f"[DEBUG] Sende join an Server mit ID: {self.player_id}")
        self.network.send("join", {"name": self.player_id})

    def send_chat_message(self):
        text = self.chat_entry.get().strip()
        if text:
            self.network.send("chat", {"text": text, "sender": self.player_id})
            self.chat_entry.delete(0, tk.END)

    def reveal_card(self, idx):
        if not self.is_my_turn:
            self.status_label.config(text="Nicht dein Zug!")
            print("[DEBUG] Karte konnte nicht aufgedeckt werden – nicht dein Zug!")
            return

        if self.revealed[idx]:
            print(f"[DEBUG] Karte {idx} ist bereits aufgedeckt.")
            return

        print(f"[DEBUG] Aufdecken von Karte {idx}")
        self.revealed[idx] = True
        self.update_gui()
        self.network.send("reveal_card", {"data": {"index": idx}})

    def handle_server_message(self, message):
        msg_type = message.get("type")
        data = message.get("data", message)

        print(f"[DEBUG] Nachricht vom Server: {msg_type} – {data}")

        if msg_type == "start":
            self.hand = data.get("hand", self.hand)
            self.player_id = str(data.get("player_id"))
            self.status_label.config(text="Spiel gestartet")
            self.update_gui()

        elif msg_type == "chat":
            self.display_chat(data.get("sender", "?"), data.get("text", ""))

        elif msg_type == "reveal_result":
            idx = data.get("data", {}).get("index")
            player = message.get("player")
            if idx is not None:
                self.revealed[idx] = True
                print(f"[DEBUG] Karte {idx} wurde aufgedeckt von Spieler {player}")
            self.update_gui()

        elif msg_type == "card_drawn":
            card = data.get("card")
            if card is not None:
                self.hand.append(card)
            self.update_gui()

        elif msg_type == "turn":
            current = data.get("player")
            print(f"[DEBUG] Aktueller Zugspieler laut Server: {current}")
            self.is_my_turn = (str(current) == str(self.player_id))
            print(f"[DEBUG] Bin ich dran? {self.is_my_turn}")
            if self.is_my_turn:
                self.status_label.config(text="Du bist am Zug!")
            else:
                self.status_label.config(text=f"{current} ist am Zug")
            self.update_gui()

        elif msg_type == "deck_update":
            deck_count = data.get("deck_count", "?")
            self.deck_label.config(text=f"Stapel: {deck_count} Karten")

    def update_gui(self):
        print(f"[DEBUG] update_gui: is_my_turn={self.is_my_turn}, revealed={self.revealed}")
        for i, btn in enumerate(self.card_buttons):
            val = self.hand[i] if self.revealed[i] else "?"
            btn.config(text=val)

            # Nur Buttons aktivieren, wenn Spieler am Zug ist und Karte nicht aufgedeckt wurde
            if self.is_my_turn and not self.revealed[i]:
                btn.config(state=tk.NORMAL)
            else:
                btn.config(state=tk.DISABLED)

    def display_chat(self, sender, message):
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f"{sender}: {message}\n")
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)
