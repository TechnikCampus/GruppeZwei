import tkinter as tk
from tkinter import messagebox, simpledialog
from PIL import Image, ImageTk
import os
from Server_Client import NetworkClient
from class_player import Player
import threading
import time

PORT = 65435


class GameGUI:
    def __init__(self, root, server_ip="127.0.0.1", server_port=65433):
        self.root = root
        self.root.title("Skyjo Client")
        self.network = NetworkClient(server_ip, server_port, self.handle_server_message)

        self.player = None
        self.current_player = None

        self.kartenbilder = self.lade_kartenbilder("karten")
        self.card_labels = [[None for _ in range(4)] for _ in range(3)]
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
        bilder = {}
        for datei in os.listdir(pfad):
            if datei.endswith(".png"):
                key = datei.replace("card_", "").replace(".png", "")
                try:
                    image = Image.open(os.path.join(pfad, datei)).resize((60, 90))
                    bilder[key] = ImageTk.PhotoImage(image)
                except Exception as e:
                    print(f"Fehler beim Laden von {datei}: {e}")
        return bilder

    def build_gui(self):

        # Deck- und Ablagestapel hinzufügen
        self.deck_image = tk.Label(self.root, image=self.kartenbilder.get("back"))
        self.deck_image.grid(row=0, column=5, padx=10, pady=10)
        self.deck_label = tk.Label(self.root, text="Zugstapel")
        self.deck_label.grid(row=1, column=5)

        self.discard_image = tk.Label(self.root, image=self.kartenbilder.get("back"))
        self.discard_image.grid(row=2, column=5, padx=10, pady=10)
        self.discard_label = tk.Label(self.root, text="Ablagestapel")
        self.discard_label.grid(row=3, column=5)

        for i in range(3):
            for j in range(4):
                lbl = tk.Label(self.root, image=self.kartenbilder.get("back", None), relief=tk.RAISED, borderwidth=2)
                lbl.grid(row=i, column=j, padx=5, pady=5)
                self.card_labels[i][j] = lbl

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

        print(f"[DEBUG] Nachricht vom Server: {msg_type} – {data}")

        if msg_type == "start":                                                             # Wenn Start empfangen wurde dann werden die Daten für den jeweiligen Spieler gespeichert
            self.hand = data.get("hand", self.hand)
            self.player_id = str(data.get("player_id"))
            self.status_label.config(text="Spiel gestartet")
            self.discard_pile = data.get("discard_pile", "?")
            if self.discard_pile:
                self.discard_pile_top = self.discard_pile[-1]
            else:
                self.discard_pile_top = "?"

            self.update_gui()

        elif msg_type == "chat":                                                            # Wenn Chat empfangen wurde dann wird die Nachricht und der Text geprintet
            self.display_chat(data.get("sender", "?"), data.get("text", ""))

        elif msg_type == "reveal_result":                                                   # Wenn eine Karte umgedreht wurde wird sich  der entsprechende Index geholt und geprüft ob idx ein gültiger Wert ist
            idx = data.get("data", {}).get("index")                                         #Anmerkung: muss man wahrscheinlich noch abfragen ob die jeweilige Karte schon umgedreht ist 
            player = message.get("player")
            if idx is not None:
                self.revealed[idx] = True
                print(f"[DEBUG] Karte {idx} wurde aufgedeckt von Spieler {player}")
            self.update_gui()

        elif msg_type == "card_drawn":                                                      # Wenn neue Karte gezogem wird dann wird diese Karte der Hand übergeben
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

        elif msg_type == "deck_update":                                                     # Fragt die Anzahl der Karten im Stappel ab  #Anmerkung: wahrscheinlich redundant
            deck_count = data.get("deck_count", "?")
            self.deck_label.config(text=f"Stapel: {deck_count} Karten")
            self.discard_pile_top = data.get("card", "?")
            self.update_gui()

        elif msg_type == "deck_drawn_card":
            self.discard_pile_top = data.get("card", "?")
            self.update_gui()

    def update_gui(self): 
        deck_button, discard_pile_button = self.piles                                                                  # Gibt die Kartenwerte an, falls aufgedeckt und aktiviert die Buttons wenn man dran ist
        print(f"[DEBUG] update_gui: is_my_turn={self.is_my_turn}, revealed={self.revealed}")
        for i, btn in enumerate(self.card_buttons):
            val = self.hand[i] if self.revealed[i] else "?"
            btn.config(text=val)

            # Nur Buttons aktivieren, wenn Spieler am Zug ist und Karte nicht aufgedeckt wurde
            if self.is_my_turn and not self.revealed[i]:
                btn.config(state=tk.NORMAL)
            else:
                btn.config(state=tk.DISABLED)

        if self.is_my_turn:
            deck_button.config(state=tk.NORMAL)
            discard_pile_button.config(state=tk.NORMAL)
    def update_gui(self):
        for i in range(3):
            for j in range(4):
                val = self.player.grid[i][j]
                if self.player.revealed[i][j] and val is not None:
                    bild_key = str(val)
                else:
                    bild_key = "back"
                bild = self.kartenbilder.get(bild_key, self.kartenbilder.get("back"))
                self.card_labels[i][j].config(image=bild)
                self.card_labels[i][j].image = bild  # Referenz halten


        # Deck immer rückseitig anzeigen
        if 'back' in self.kartenbilder:
            self.deck_image.config(image=self.kartenbilder['back'])
            self.deck_image.image = self.kartenbilder['back']

        # Ablagestapel: oberste Karte anzeigen, wenn vorhanden
        top_discard = self.player.hand[-1] if self.player.hand else None
        if top_discard is not None:
            bild_key = str(top_discard)
            bild = self.kartenbilder.get(bild_key, self.kartenbilder.get("back"))
            self.discard_image.config(image=bild)
            self.discard_image.image = bild

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

    def deck_draw_card(self):
        if not self.is_my_turn:                                                             # Abfrage ob Spieler dran ist
            self.status_label.config(text="Nicht dein Zug!")                                #Anmerkung: ist bestimmt eleganter zu lösen!
            print("[DEBUG] Karte konnte nicht aufgedeckt werden – nicht dein Zug!")
            return

        self.network.send("deck_draw_card")

        # self.discard_pile.append(self.deck.pop(0))

    def discard_pile_draw(self):
        pass
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
