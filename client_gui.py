import tkinter as tk
from tkinter import simpledialog
from Server_Client import NetworkClient

PORT = 65435


class GameGUI:
    def __init__(self, root, server_ip, server_port):
        self.root = root
        self.root.title("Skyjo Client")

        self.player_id = None                                       # vom Server zu geteilte ID
        self.hand = ["?"] * 12                                      # Kartendeck des einzelnen
        self.revealed = [False] * 12                                # Liste der umgedrehten Karten
        self.is_my_turn = False                                     # Abfrage: bin ich am Zug?

        self.card_buttons = []                                      # liste aller Tkinter Buttons
        self.chat_entry = tk.Entry(self.root, width=40)                  # initialisiert Eingabefeld für Chat
        self.chat_button = tk.Button(self.root, text="Senden", command=self.send_chat_message)   # Senden Button für Chat
        self.chat_display = tk.Text(self.root, height=10, width=60, state=tk.DISABLED)           # Textfeld für Chatnachrichten
        self.status_label = tk.Label(self.root, text="Status")                                   # Verbindungsstatus
        self.deck_label = tk.Label(self.root, text="Stapel: ? Karten")                      # Zeigt Anzahl Karten im Deck
        self.deck_label.grid(row=6, column=0, columnspan=2)                                 # Plaziert Label im Grid
        self.build_gui()

        self.prompt_player_name()                                                           # Spielernamenabfrage
        self.network = NetworkClient(server_ip, server_port, self.handle_server_message, self.on_connected) # erstellt den Client für die Kommunikation
        self.root.after(100, self.connect_to_server)                                        # Startet Verbindung zum Server nach 100ms

    def build_gui(self):
        for i in range(3):                                                                  # Zeilen
            for j in range(4):                                                              # Spalten
                idx = i * 4 + j                                                             # Indexberechnung
                btn = tk.Button(self.root, text="?", width=6, state=tk.DISABLED,            # Erstellt Karte als Button mit "?"
                                command=lambda idx=idx: self.reveal_card(idx))
                btn.grid(row=i, column=j, padx=5, pady=5)                                   # Platziert Button im Grid
                self.card_buttons.append(btn)                                               # Fügt aktuellen Button der Liste hinzu

        self.deck_label.grid(row=1, column=4, rowspan=2, padx=10, pady=10, sticky="n")      # Platziert Label des Kartenstappel im Grid

                                                                                            # Button hinzufügen für Kartenstappel bzw neue Karte Ziehen

        self.status_label.grid(row=3, column=0, columnspan=4)                               # Platziert Status Label im Grid
        self.chat_display.grid(row=4, column=0, columnspan=4)                               # Platziert Chat im Grid
        self.chat_entry.grid(row=5, column=0, columnspan=3)                                 # Platziert Eingabefeld im Grid
        self.chat_button.grid(row=5, column=3)                                              # Platziert Sende-Button im Grid

    def prompt_player_name(self):                                                           # Fragt den Spieler nach seinem Namen
        name = None
        while not name:
            name = simpledialog.askstring("Spielername", "Gib deinen Spielernamen ein:")
        self.player_id = str(name)                                                          #Anmerkung: Name wird als ID gespeichert, am besten noch ändern aufgrund von leserlichkeit
        print(f"[DEBUG] Spielername gesetzt: {self.player_id}")

    def connect_to_server(self):                                                            # Baut Verbindung zum Server, wenn nicht dann Fehlermeldung
        connected = self.network.connect()
        if not connected:
            self.status_label.config(text="Verbindung fehlgeschlagen")

    def on_connected(self):                                                                 # Gibt dem Server den Name ds Spielers
        self.status_label.config(text="Verbunden mit Server")
        print(f"[DEBUG] Sende join an Server mit ID: {self.player_id}")                     #Anmerkung: Name wird als ID gespeichert, Ändern!
        self.network.send("join", {"name": self.player_id})

    def send_chat_message(self):                                                            # Wird beim Senden-Button ausgefuerht
        text = self.chat_entry.get().strip()                                                # holt den Text aus dem Eingabefeld und entfernt unnoetige Zeichen
        if text:
            self.network.send("chat", {"text": text, "sender": self.player_id})             #Anmerkung: Name wird als ID gespeichert, Ändern! # Sendet Nachricht an den Server
            self.chat_entry.delete(0, tk.END)                                               # loescht Nachricht nach dem Senden

    def reveal_card(self, idx):
        if not self.is_my_turn:                                                             # Abfrage ob Spieler dran ist
            self.status_label.config(text="Nicht dein Zug!")                                #Anmerkung: ist bestimmt eleganter zu lösen!
            print("[DEBUG] Karte konnte nicht aufgedeckt werden – nicht dein Zug!")
            return

        if self.revealed[idx]:                                                              # Abfrage ob Karte schon aufgedeckt ist
            print(f"[DEBUG] Karte {idx} ist bereits aufgedeckt.")
            return

        print(f"[DEBUG] Aufdecken von Karte {idx}")                                         # Falls beide Abfragen nein sind, wir die Karte aufgedeckt und an den Server weitergeleitet
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
