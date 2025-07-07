
import tkinter as tk
from tkinter import simpledialog, PhotoImage
from Server_Client import NetworkClient
import time
from PIL import Image, ImageTk

PORT = 65435

def init_image(image_path, width=60, height=90):
    image = Image.open(image_path)
    image = image.resize((width, height))
    return ImageTk.PhotoImage(image)

class GameGUI:
    def __init__(self, root, server_ip, server_port):
        self.root = root
        self.root.title("Skyjo Client")
        self.root.geometry("700x400")

        self.images = {}  # Karten
        for i in range(-2, 13):
            self.images[i] = init_image(f"assets/card_{i}.png")
        self.images["?"] = init_image("assets/card_back.png")

        # Load images
        self.background_image_initial = PhotoImage(file="assets/Spielhintergrund.png")
        self.background_image_connected = PhotoImage(file="assets/Lobby.png")

        # Create a label to display the background image
        self.background_label = tk.Label(self.root, image=self.background_image_initial)
        self.background_label.place(x=0, y=0, relwidth=1, relheight=1)

        self.player_id = None                                       # vom Server zu geteilte ID
        self.hand = ["?"] * 12                                      # Kartendeck des einzelnen
        self.revealed = [False] * 12                                # Liste der umgedrehten Karten
        self.is_my_turn = False                                     # Abfrage: bin ich am Zug?
        self.discard_pile = []
        self.discard_pile_top = "?"
        self.draw_count = 0
        self.start_count = 0
        self.score_overall = 0                                   # Gesamtpunkte
        self.statusGame = True
        self.round_over_sent = False

        self.card_buttons = []                                      # liste aller Tkinter Buttons
        self.piles = []
        self.chat_entry = tk.Entry(self.root, width=40)                  # initialisiert Eingabefeld für Chat
        self.chat_button = tk.Button(self.root, text="Senden", command=self.send_chat_message)   # Senden Button für Chat
        self.chat_display = tk.Text(self.root, height=10, width=60, state=tk.DISABLED)           # Textfeld für Chatnachrichten
        self.status_label = tk.Label(self.root, text="Status")                                   # Verbindungsstatus
        self.deck_label = tk.Label(self.root, text="Stapel: ? Karten")                      # Zeigt Anzahl Karten im Deck
        self.deck_label.grid(row=6, column=0, columnspan=2)                                 # Plaziert Label im Grid
        self.score = tk.Label(self.root, text="Deine Punkte:")
        self.score.grid(row=6, column=2, columnspan=2)
        self.build_gui()

        self.prompt_player_name()                                                           # Spielernamenabfrage
        self.network = NetworkClient(server_ip, server_port, self.handle_server_message, self.on_connected)  # erstellt den Client für die Kommunikation
        self.root.after(100, self.connect_to_server)                                        # Startet Verbindung zum Server nach 100ms

    def build_gui(self):
        for i in range(3):                                                                  # Zeilen
            for j in range(4):                                                              # Spalten
                idx = i * 4 + j                                                             # Indexberechnung
                btn = tk.Button(self.root, text="?", state=tk.DISABLED,            # Erstellt Karte als Button mit "?"
                                command=lambda idx=idx: self.reveal_card(idx))
                btn.grid(row=i, column=j, padx=5, pady=5)                                   # Platziert Button im Grid
                self.card_buttons.append(btn)                                               # Fügt aktuellen Button der Liste hinzu

        deck_button = tk.Button(self.root, text="?", state=tk.DISABLED, command=self.deck_draw_card)      # Platziert Label des Kartenstappel im Grid
        deck_button.grid(row=1, column=5, padx=5, pady=5)                                # Platziert Button im Grid
        self.piles.append(deck_button)

        discard_pile_button = tk.Button(self.root, text="?", state=tk.DISABLED, command=self.discard_pile_draw)      # Platziert Label des Kartenstappel im Grid
        discard_pile_button.grid(row=2, column=5, padx=5, pady=5)
        self.piles.append(discard_pile_button)

        self.status_label.grid(row=3, column=0, columnspan=4)                               # Platziert Status Label im Grid
        self.chat_display.grid(row=4, column=0, columnspan=4)                               # Platziert Chat im Grid
        self.chat_entry.grid(row=5, column=0, columnspan=3)                                 # Platziert Eingabefeld im Grid
        self.chat_button.grid(row=5, column=3)                                              # Platziert Sende-Button im Grid

    def prompt_player_name(self):                                                           # Fragt den Spieler nach seinem Namen
        name = None
        while not name:
            name = simpledialog.askstring("Spielername", "Gib deinen Spielernamen ein:")
        self.player_id = str(name)                                                          #Anmerkung: Name wird als ID gespeichert, am besten noch ändern aufgrund von leserlichkeit
        # print(f"[DEBUG] Spielername gesetzt: {self.player_id}")

    def connect_to_server(self):                                                            # Baut Verbindung zum Server, wenn nicht dann Fehlermeldung
        connected = self.network.connect()
        if not connected:
            self.status_label.config(text="Verbindung fehlgeschlagen")
        else:
            self.on_connected()

    def on_connected(self):                                                                 # Gibt dem Server den Name ds Spielers
        self.status_label.config(text="Verbunden mit Server")

                  #Anmerkung: Name wird als ID gespeichert, Ändern!

        self.background_label.config(image=self.background_image_connected)
        # print(f"[DEBUG] Sende join an Server mit ID: {self.player_id}")                     #Anmerkung: Name wird als ID gespeichert, Ändern!

        self.network.send("join", {"name": self.player_id})

    def send_chat_message(self):                                                            # Wird beim Senden-Button ausgefuerht
        text = self.chat_entry.get().strip()                                                # holt den Text aus dem Eingabefeld und entfernt unnoetige Zeichen
        if text:
            self.network.send("chat", {"text": text, "sender": self.player_id})             #Anmerkung: Name wird als ID gespeichert, Ändern! # Sendet Nachricht an den Server
            self.chat_entry.delete(0, tk.END)                                               # loescht Nachricht nach dem Senden

    def reveal_card(self, idx):
        if not self.is_my_turn:                                                             # Abfrage ob Spieler dran ist
            self.status_label.config(text="Nicht dein Zug!")                                #Anmerkung: ist bestimmt eleganter zu lösen!
            # print("[DEBUG] Karte konnte nicht aufgedeckt werden – nicht dein Zug!")
            return

        print(f"[DEBUG] Aufdecken von Karte {idx}")                                         # Falls beide Abfragen nein sind, wir die Karte aufgedeckt und an den Server weitergeleitet
        self.revealed[idx] = True
        self.update_gui()
        self.network.send("reveal_card", {"data": {"index": idx}})
        self.start_count += 1

    def handle_server_message(self, message):                                               # Methode zum Empfangen vom Server
        msg_type = message.get("type")                                                      # speichert Typ und Daten der Nachricht ab
        data = message.get("data", message)

        # print(f"[DEBUG] Nachricht vom Server: {msg_type} – {data}")

        if msg_type == "start":                                                             # Wenn Start empfangen wurde dann werden die Daten für den jeweiligen Spieler gespeichert
            self.hand = data.get("hand", self.hand)
            self.player_id = str(data.get("player_id"))
            self.status_label.config(text="Spiel gestartet")
            self.discard_pile = data.get("discard_pile", "?")
            if self.discard_pile:
                self.discard_pile_top = self.discard_pile[-1]
            else:
                self.discard_pile_top = "?"

            self.revealed = [False] * 12
            self.round_over_sent = False
            self.start_count = 0
            self.is_my_turn = False
            self.draw_count = 0
            self.statusGame = True
            self.update_gui()

        elif msg_type == "new_round":
            self.status_label.config(text="Es beginnt eine neue Runde!")
            if not all(self.revealed):
                # Nicht alle Karten aufgedeckt → alle aufdecken und Punkte berechnen
                round_score = sum(val for val in self.hand if val != 13)  # zähle alle Karten außer „X“
                self.score_overall += round_score
                self.score.config(text=f"Deine Punkte: {self.score_overall}")
                for i, btn in enumerate(self.card_buttons):
                    if self.hand[i] != 13:
                        val = self.hand[i]
                        btn.config(text=val)
                    else:
                        btn.config(text="X")
            time.sleep(5)
            self.hand = data.get("hand", self.hand)
            self.player_id = str(data.get("player_id"))
            self.status_label.config(text="Spiel gestartet")
            self.discard_pile = data.get("discard_pile", "?")
            if self.discard_pile:
                self.discard_pile_top = self.discard_pile[-1]
            else:
                self.discard_pile_top = "?"

            self.revealed = [False] * 12
            self.round_over_sent = False
            self.start_count = 0
            self.is_my_turn = False
            self.draw_count = 0
            self.statusGame = True
            self.update_gui()

        elif msg_type == "chat":                                                            # Wenn Chat empfangen wurde dann wird die Nachricht und der Text geprintet
            self.display_chat(data.get("sender", "?"), data.get("text", ""))

        elif msg_type == "reveal_result":                                                   # Wenn eine Karte umgedreht wurde wird sich  der entsprechende Index geholt und geprüft ob idx ein gültiger Wert ist
            idx = data.get("data", {}).get("index")                                         #Anmerkung: muss man wahrscheinlich noch abfragen ob die jeweilige Karte schon umgedreht ist
            player = message.get("player")
            if idx is not None:
                self.revealed[idx] = True
                # print(f"[DEBUG] Karte {idx} wurde aufgedeckt von Spieler {player}")
            self.update_gui()

        elif msg_type == "card_drawn":                                                      # Wenn neue Karte gezogem wird dann wird diese Karte der Hand übergeben
            card = data.get("card")
            if card is not None:
                self.hand.append(card)
            self.update_gui()

        elif msg_type == "turn":                                                            # wenn ein neuer Spieler dran ist, wird geprüft ob man selbst derjenige ist und dementsprechend wird die Statusleiste aktualisiert
            current = data.get("player")
            # print(f"[DEBUG] Aktueller Zugspieler laut Server: {current}")
            self.is_my_turn = (str(current) == str(self.player_id))
            # print(f"[DEBUG] Bin ich dran? {self.is_my_turn}")
            self.draw_count = 0
            if self.is_my_turn:
                self.status_label.config(text="Du bist am Zug!")
            else:

                self.status_label.config(text=f"{data.get('name', '?')} ist am Zug")

            self.update_gui()

        elif msg_type == "deck_update":                                                     # Fragt die Anzahl der Karten im Stappel ab  #Anmerkung: wahrscheinlich redundant
            deck_count = data.get("deck_count", "?")
            self.deck_label.config(text=f"Stapel: {deck_count} Karten")
            self.discard_pile_top = data.get("card", "?")
            self.update_gui()

        elif msg_type == "deck_drawn_card":
            self.discard_pile_top = data.get("card", "?")
            self.update_gui()
            self.draw_count += 1

        elif msg_type == "deck_switched_card":

            self.hand = data.get("hand", self.hand)
            idx = data.get("index")
            if idx is not None:
                self.revealed[idx] = True
            self.update_gui()

        elif msg_type == "threesome":
            self.hand = data.get("hand", self.hand)
            self.update_gui()

        elif msg_type == "game_over":                                                      # Wenn Runde zu Ende ist, wird der Spielername und die Punkte angezeigt
            print("[DEBUG] game_over empfangen, Fenster wird in 6 Sekunden geschlossen.")
            if not all(self.revealed):
                # Nicht alle Karten aufgedeckt → alle aufdecken und Punkte berechnen
                round_score = sum(val for val in self.hand if val != 13)  # zähle alle Karten außer „X“
                self.score_overall += round_score
                self.score.config(text=f"Deine Punkte: {self.score_overall}")
                for i, btn in enumerate(self.card_buttons):
                    if self.hand[i] != 13:
                        val = self.hand[i]
                        btn.config(text=val)
                    else:
                        btn.config(text="X")
            time.sleep(5)
            self.statusGame = False
            self.status_label.config(text="Spiel beendet!")
            self.root.after(1000, self.root.destroy)

    def update_gui(self):
        deck_button, discard_pile_button = self.piles                                                                  # Gibt die Kartenwerte an, falls aufgedeckt und aktiviert die Buttons wenn man dran ist
        # print(f"[DEBUG] update_gui: is_my_turn={self.is_my_turn}, revealed={self.revealed}")
        for i, btn in enumerate(self.card_buttons):
            val = self.hand[i] if self.revealed[i] else "?"

            btn.config(text=val, image=self.images.get(val, self.images["?"]))  # Zeigt die Karte an, wenn sie aufgedeckt ist

            # Nur Buttons aktivieren, wenn Spieler am Zug ist und Karte nicht aufgedeckt wurde
            if self.is_my_turn and self.hand is not None:
                btn.config(state=tk.NORMAL)
            else:
                btn.config(state=tk.DISABLED)

            if val == 13:
                btn.config(state=tk.DISABLED)
                btn.config(text="X")  # Zeigt X an, wenn diese Karte nicht mehr verfügbar ist

        if self.is_my_turn and self.draw_count < 1:  # Abfrage ob Spieler am Zug ist und ob er schon eine Karte gezogen hat
            deck_button.config(state=tk.NORMAL)
            discard_pile_button.config(state=tk.NORMAL)
        elif self.is_my_turn and self.draw_count >= 1:  # Abfrage ob Spieler am Zug ist und ob er schon eine Karte gezogen hat
            deck_button.config(state=tk.DISABLED)
            discard_pile_button.config(state=tk.NORMAL)
        else:
            deck_button.config(state=tk.DISABLED)
            discard_pile_button.config(state=tk.DISABLED)

        discard_pile_button.config(text=str(self.discard_pile_top))

        self.score.config(text=f"Deine Punkte: {self.count_score()}")
        self.check_for_end()  # Überprüft, ob das Spiel zu Ende ist

        deck_button.config(image=self.images["?"])  # Zeigt das Bild der Karte an, wenn sie aufgedeckt ist
        discard_pile_button.config(image=self.images.get(self.discard_pile_top, self.images["?"]))  # Zeigt das Bild der

        self.count_score()


    def display_chat(self, sender, message):
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f"{sender}: {message}\n")
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)

    def deck_draw_card(self):
        if not self.is_my_turn:                                                             # Abfrage ob Spieler dran ist
            self.status_label.config(text="Nicht dein Zug!")                                #Anmerkung: ist bestimmt eleganter zu lösen!
            # print("[DEBUG] Karte konnte nicht aufgedeckt werden – nicht dein Zug!")
            return

        self.network.send("deck_draw_card")

    def discard_pile_draw(self):
        self.network.send("discard_pile_draw")

    def count_score(self):
        temp = 0
        for i in range(12):
            if self.revealed[i] and self.hand[i] != 13 and self.statusGame:  # Wenn Karte aufgedeckt und nicht 13 (X)
                temp += self.hand[i]
        temp += self.score_overall
        return temp

    def check_for_end(self):
        if all(self.revealed) and not self.round_over_sent:
            self.round_over_sent = True
            self.network.send("round_over", {"player": self.player_id})
            self.status_label.config(text="Spiel beendet! Du hast alle Karten aufgedeckt.")
            print(f"[DEBUG] Spieler {self.player_id} hat alle Karten aufgedeckt – Spielende.")
            self.score_overall = self.count_score()
            self.score.config(text=f"Deine Punkte: {self.score_overall}")
            self.status_label.config(text="DU hast alle Karten aufgedeckt, deine Runde ist vorbei")
