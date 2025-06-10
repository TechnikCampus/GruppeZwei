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

        # Spielhintergrund
        try:
            bg = ImageTk.PhotoImage(Image.open("Spielhintergrund.png"))
            label_bg = tk.Label(self.root, image=bg)
            label_bg.image = bg
            label_bg.place(relwidth=1, relheight=1)
            label_bg.lower()  # ganz nach unten
        except Exception as e:
            print(f"[WARN] Spielhintergrund.png konnte nicht geladen werden: {e}")

        self.network = NetworkClient(server_ip, server_port, self.handle_server_message)

        self.player = None
        self.current_player = None

        # Kartenbilder laden
        self.kartenbilder = self.lade_kartenbilder("karten")
        self.card_labels = [[None for _ in range(4)] for _ in range(3)]

        # Chat & Status
        self.chat_entry = tk.Entry(root, width=40)
        self.chat_button = tk.Button(root, text="Senden", command=self.send_chat_message)
        self.chat_display = tk.Text(root, height=10, width=60, state=tk.DISABLED)
        self.status_label = tk.Label(root, text="Status")
        self.timer_label = tk.Label(root, text="Zug-Timer: -")
        self.timer_active = False

        self.build_gui()
        self.prompt_player_name()
        self.root.after(100, self.connect_to_server)

    def lade_kartenbilder(self, pfad):
        from PIL import Image
        import os
        bilder = {}
        for datei in os.listdir(pfad):
            if datei.endswith(".png"):
                key = datei.replace("card_", "").replace(".png", "")
                try:
                    img = Image.open(os.path.join(pfad, datei)).resize((60, 90))
                    bilder[key] = ImageTk.PhotoImage(img)
                except Exception as e:
                    print(f"Fehler beim Laden von {datei}: {e}")
        return bilder

    def build_gui(self):
        # Deck- und Ablagestapel
        self.deck_image = tk.Label(self.root, image=self.kartenbilder.get("back"))
        self.deck_image.grid(row=0, column=5, padx=10, pady=10)
        tk.Label(self.root, text="Zugstapel").grid(row=1, column=5)

        self.discard_image = tk.Label(self.root, image=self.kartenbilder.get("back"))
        self.discard_image.grid(row=2, column=5, padx=10, pady=10)
        tk.Label(self.root, text="Ablagestapel").grid(row=3, column=5)

        # Spielfeld
        for i in range(3):
            for j in range(4):
                lbl = tk.Label(self.root, image=self.kartenbilder.get("back"), relief=tk.RAISED, borderwidth=2)
                lbl.grid(row=i, column=j, padx=5, pady=5)
                self.card_labels[i][j] = lbl

        # Timer & Status
        self.timer_label.grid(row=3, column=0, columnspan=2)
        self.status_label.grid(row=3, column=2, columnspan=2)

        # Chat
        chat_frame = tk.Frame(self.root)
        chat_frame.grid(row=4, column=0, columnspan=4, pady=10)
        self.chat_display.pack(in_=chat_frame)
        self.chat_entry.pack(in_=chat_frame, side=tk.LEFT, padx=(0,5))
        self.chat_button.pack(in_=chat_frame, side=tk.RIGHT)

        self.root.bind("<Return>", lambda e: self.send_chat_message())
        self.root.bind("<Escape>", lambda e: self.root.quit())

    def prompt_player_name(self):
        name = None
        while not name:
            name = simpledialog.askstring("Spielername", "Gib deinen Spielernamen ein:")
        from class_player import Player
        self.player = Player(name)
        self.root.title(f"Skyjo – {self.player.id}")

    def connect_to_server(self):
        if self.network.connect():
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
            self.display_chat("System", f"Spiel startet – du bist {self.player.id}")
        elif msg_type == "card_drawn":
            card = data.get("card")
            if card is not None:
                self.player.hand.append(card)
                self.display_chat("System", f"Du hast gezogen: {card}")
        elif msg_type == "reveal_result":
            pos = data.get("data", {})
            r, c = pos.get("row"), pos.get("col")
            if r is not None and c is not None:
                self.player.revealed[r][c] = True
        elif msg_type == "chat":
            self.display_chat(data.get("sender", "?"), data.get("text", ""))
        elif msg_type == "game_state":
            self.current_player = data.get("current_player")
        self.update_gui()

    def update_gui(self):
        # Karten aktualisieren
        for i in range(3):
            for j in range(4):
                if self.player.revealed[i][j]:
                    key = str(self.player.grid[i][j])
                else:
                    key = "back"
                img = self.kartenbilder.get(key, self.kartenbilder["back"])
                lbl = self.card_labels[i][j]
                lbl.config(image=img)
                lbl.image = img

        # Stapel
        self.deck_image.config(image=self.kartenbilder["back"])
        self.discard_image.config(
            image=self.kartenbilder.get(
                str(self.player.hand[-1]) if self.player.hand else "back",
                self.kartenbilder["back"]
            )
        )

        # Status & Timer
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
        if getattr(self, "timer_running", False):
            return
        self.timer_running = True
        import threading, time
        def countdown():
            t = duration
            while t > 0 and self.timer_running:
                self.timer_label.config(text=f"Zug-Timer: {t}s")
                time.sleep(1)
                t -= 1
            if self.timer_running:
                self.timer_label.config(text="Zeit abgelaufen!")
            self.timer_running = False
        threading.Thread(target=countdown, daemon=True).start()
