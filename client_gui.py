import tkinter as tk
from tkinter import simpledialog
from PIL import Image, ImageTk
from Server_Client import NetworkClient

PORT = 65435

class GameGUI:
    def __init__(self, root, server_ip, server_port):
        self.root = root
        self.root.title("Skyjo Client")
        self.root.geometry("800x600")
        self.root.resizable(False, False)

        # Hintergrundbild
        self.bg_image = ImageTk.PhotoImage(Image.open("Lobby.png"))
        self.bg_label = tk.Label(self.root, image=self.bg_image)
        self.bg_label.place(relwidth=1, relheight=1)

        self.main_frame = tk.Frame(self.root, bg="white")
        self.main_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        self.player_id = None
        self.hand = ["?"] * 12
        self.revealed = [False] * 12
        self.is_my_turn = False
        self.discard_pile = []
        self.discard_pile_top = "?"

        self.card_buttons = []
        self.piles = []
        self.chat_entry = tk.Entry(self.main_frame, width=40)
        self.chat_button = tk.Button(self.main_frame, text="Senden", command=self.send_chat_message)
        self.chat_display = tk.Text(self.main_frame, height=6, width=55, state=tk.DISABLED)
        self.status_label = tk.Label(self.main_frame, text="Status")
        self.deck_label = tk.Label(self.main_frame, text="Stapel: ? Karten")

        self.build_gui()
        self.prompt_player_name()
        self.network = NetworkClient(server_ip, server_port, self.handle_server_message, self.on_connected)
        self.root.after(100, self.connect_to_server)

    def build_gui(self):
        # Karten-Grid
        card_frame = tk.Frame(self.main_frame)
        for i in range(3):
            for j in range(4):
                idx = i * 4 + j
                btn = tk.Button(card_frame, text="?", width=6, height=2, state=tk.DISABLED,
                                command=lambda idx=idx: self.reveal_card(idx))
                btn.grid(row=i, column=j, padx=5, pady=5)
                self.card_buttons.append(btn)
        card_frame.pack(pady=10)

        # Stapel
        pile_frame = tk.Frame(self.main_frame)
        deck_button = tk.Button(pile_frame, text="?", width=6, height=2, state=tk.DISABLED, command=self.deck_draw_card)
        discard_button = tk.Button(pile_frame, text="?", width=6, height=2, state=tk.DISABLED, command=self.discard_pile_draw)
        deck_button.grid(row=0, column=0, padx=20)
        discard_button.grid(row=0, column=1, padx=20)
        pile_frame.pack(pady=5)

        self.piles = [deck_button, discard_button]
        self.deck_label.pack(pady=5)
        self.status_label.pack(pady=5)

        # Chat
        self.chat_display.pack(pady=5)
        chat_input_frame = tk.Frame(self.main_frame)
        self.chat_entry.pack(in_=chat_input_frame, side=tk.LEFT, padx=5)
        self.chat_button.pack(in_=chat_input_frame, side=tk.LEFT)
        chat_input_frame.pack(pady=5)

    def prompt_player_name(self):
        name = None
        while not name:
            name = simpledialog.askstring("Spielername", "Gib deinen Spielernamen ein:")
        self.player_id = str(name)

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
        if not self.is_my_turn or self.revealed[idx]:
            return
        self.revealed[idx] = True
        self.update_gui()
        self.network.send("reveal_card", {"data": {"index": idx}})

    def handle_server_message(self, message):
        msg_type = message.get("type")
        data = message.get("data", message)

        if msg_type == "start":
            self.hand = data.get("hand", self.hand)
            self.player_id = str(data.get("player_id"))
            self.status_label.config(text="Spiel gestartet")
            self.discard_pile = data.get("discard_pile", "?")
            self.discard_pile_top = self.discard_pile[-1] if self.discard_pile else "?"
            self.update_gui()

        elif msg_type == "chat":
            self.display_chat(data.get("sender", "?"), data.get("text", ""))

        elif msg_type == "reveal_result":
            idx = data.get("data", {}).get("index")
            if idx is not None:
                self.revealed[idx] = True
            self.update_gui()

        elif msg_type == "card_drawn":
            card = data.get("card")
            if card is not None:
                self.hand.append(card)
            self.update_gui()

        elif msg_type == "turn":
            current = data.get("player")
            self.is_my_turn = (str(current) == str(self.player_id))
            self.status_label.config(text="Du bist am Zug!" if self.is_my_turn else f"{data.get('name', '?')} ist am Zug")
            self.update_gui()

        elif msg_type == "deck_update":
            self.deck_label.config(text=f"Stapel: {data.get('deck_count', '?')} Karten")

    def update_gui(self):
        deck_button, discard_button = self.piles
        for i, btn in enumerate(self.card_buttons):
            val = self.hand[i] if self.revealed[i] else "?"
            btn.config(text=val)
            btn.config(state=tk.NORMAL if self.is_my_turn and not self.revealed[i] else tk.DISABLED)

        deck_button.config(state=tk.NORMAL if self.is_my_turn else tk.DISABLED)
        discard_button.config(state=tk.NORMAL if self.is_my_turn else tk.DISABLED)
        discard_button.config(text=str(self.discard_pile_top))

    def display_chat(self, sender, message):
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f"{sender}: {message}\n")
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)

    def deck_draw_card(self):
        pass

    def discard_pile_draw(self):
        pass
