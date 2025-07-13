import tkinter as tk
from tkinter import simpledialog, PhotoImage
from Server_Client import NetworkClient
import time
from PIL import Image, ImageTk
import os

PORT = 65435  # Standardport für die Verbindung zum Server


# Lädt und skaliert ein Bild (z. B. Kartenbild)
def init_image(image_path, width=60, height=90):
    image = Image.open(image_path)
    image = image.resize((width, height))
    return ImageTk.PhotoImage(image)


class GameGUI:
    def __init__(self, root, server_ip, server_port):
        self.root = root
        self.root.title("Skyjo Client")
        self.root.geometry("700x600")

        # Kartenbilder vorbereiten
        self.images = {}
        for i in range(-2, 13):
            self.images[i] = init_image(f"assets/card_{i}.png")
        self.images["?"] = init_image("assets/card_back.png")

        # Hintergrundbilder laden
        self.background_image_initial = PhotoImage(file="assets/Spielhintergrund.png")
        self.background_image_connected = PhotoImage(file="assets/Lobby.png")

        # Label zum Anzeigen des Hintergrundbilds
        self.background_label = tk.Label(self.root, image=self.background_image_initial)
        self.background_label.place(x=0, y=0, relwidth=1, relheight=1)

        # Spielstatus-Variablen
        self.player_id = None
        self.hand = ["?"] * 12  # Spielerhand mit 12 verdeckten Karten
        self.revealed = [False] * 12  # Welche Karten wurden aufgedeckt?
        self.is_my_turn = False  # Ist dieser Client gerade am Zug?
        self.discard_pile = []  # Ablagestapel (gesamter Verlauf)
        self.discard_pile_top = "?"  # oberste Karte vom Ablagestapel
        self.draw_count = 0
        self.start_count = 0
        self.score_overall = 0  # Punkte über Runden hinweg
        self.statusGame = True  # Spiel aktiv
        self.round_over_sent = False  # Wurde "round_over" gesendet?
        self.points_reached = False

        # GUI-Elemente (Buttons etc.)
        self.card_buttons = []  # Spielfeldkarten
        self.piles = []  # Deck + Ablagestapel

        self.chat_entry = tk.Entry(self.root, width=40)  # Texteingabe für Chat
        self.chat_button = tk.Button(self.root, text="Senden", command=self.send_chat_message)
        self.chat_display = tk.Text(self.root, height=10, width=60, state=tk.DISABLED)

        self.status_label = tk.Label(self.root, text="Status")  # Statusanzeige
        self.deck_label = tk.Label(self.root, text="Stapel: ? Karten")  # Zeigt Deckanzahl an
        self.deck_label.grid(row=6, column=0, columnspan=2)

        self.score = tk.Label(self.root, text="Deine Punkte:")
        self.score.grid(row=6, column=2, columnspan=2)

        self.build_gui()  # GUI aufbauen (Kartenbuttons, Chat usw.)
        self.prompt_player_name()  # Spielername abfragen

        # Netzwerkverbindung vorbereiten
        self.network = NetworkClient(server_ip, server_port, self.handle_server_message, self.on_connected)
        self.root.after(100, self.connect_to_server)  # Nach 100ms versuchen, zu verbinden

    def build_gui(self):
        # Kartenraster (3 Zeilen x 4 Spalten)
        for i in range(3):
            for j in range(4):
                idx = i * 4 + j
                btn = tk.Button(self.root, text="?", state=tk.DISABLED,
                                command=lambda idx=idx: self.reveal_card(idx))
                btn.grid(row=i, column=j, padx=5, pady=5)
                self.card_buttons.append(btn)

        # Stapel-Button (Deck)
        deck_button = tk.Button(self.root, text="?", state=tk.DISABLED, command=self.deck_draw_card)
        deck_button.grid(row=1, column=5, padx=5, pady=5)
        self.piles.append(deck_button)

        # Ablagestapel-Button
        discard_pile_button = tk.Button(self.root, text="?", state=tk.DISABLED, command=self.discard_pile_draw)
        discard_pile_button.grid(row=2, column=5, padx=5, pady=5)
        self.piles.append(discard_pile_button)

        # Weitere GUI-Komponenten platzieren
        self.status_label.grid(row=3, column=0, columnspan=4)
        self.chat_display.grid(row=4, column=0, columnspan=4)
        self.chat_entry.grid(row=5, column=0, columnspan=3)
        self.chat_button.grid(row=5, column=3)

    def prompt_player_name(self):
        # Name des Spielers abfragen
        name = None
        while not name:
            name = simpledialog.askstring("Spielername", "Gib deinen Spielernamen ein:")
        self.player_id = str(name)

    def connect_to_server(self):
        # Verbindungsversuch mit dem Server
        connected = self.network.connect()
        if not connected:
            self.status_label.config(text="Verbindung fehlgeschlagen")
        else:
            self.on_connected()

    def on_connected(self):
        # Wird nach erfolgreicher Verbindung aufgerufen
        self.status_label.config(text="Verbunden mit Server")
        self.background_label.config(image=self.background_image_connected)
        self.network.send("join", {"name": self.player_id})

    def send_chat_message(self):
        # Nachricht aus Eingabefeld an Server senden
        text = self.chat_entry.get().strip()
        if text:
            self.network.send("chat", {"text": text, "sender": self.player_id})
            self.chat_entry.delete(0, tk.END)

    def reveal_card(self, idx):
        if not self.is_my_turn:                                                            # Karte aufdecken (nur wenn am Zug)
            self.status_label.config(text="Nicht dein Zug!")
            # print("[DEBUG] Karte konnte nicht aufgedeckt werden – nicht dein Zug!")
            return

        print(f"[DEBUG] Aufdecken von Karte {idx}")         # Falls beide Abfragen nein sind, wir die Karte aufgedeckt und an den Server weitergeleitet

        self.revealed[idx] = True
        self.update_gui()
        self.network.send("reveal_card", {"data": {"index": idx}})
        self.start_count += 1

    def handle_server_message(self, message):
        # Verarbeitet eingehende Nachrichten vom Server
        msg_type = message.get("type")
        data = message.get("data", message)

        if msg_type == "start":
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
            # Vorbereitung für neue Runde
            self.status_label.config(text="Es beginnt eine neue Runde!")
            if not all(self.revealed):
                round_score = sum(val for val in self.hand if val != 13)
                self.score_overall += round_score
                self.score.config(text=f"Deine Punkte: {self.score_overall}")
                for i, btn in enumerate(self.card_buttons):
                    if self.hand[i] != 13:
                        val = self.hand[i] 
                        btn.config(text=val, image=self.images.get(val, self.images["?"]))
                    else:
                        btn.config(image=self.images["?"])
            time.sleep(5)
            self.hand = data.get("hand", self.hand)
            self.player_id = str(data.get("player_id"))
            nextPlayer = data.get("startPlayer", 0)
            self.status_label.config(text="Spiel gestartet")
            self.discard_pile = data.get("discard_pile", "?")
            if self.discard_pile:
                self.discard_pile_top = self.discard_pile[-1]
            else:
                self.discard_pile_top = "?"
            self.check_for_100P()
            self.revealed = [False] * 12
            self.round_over_sent = False
            self.start_count = 0
            self.is_my_turn = False
            self.draw_count = 0
            self.statusGame = True
            self.update_gui()

        elif msg_type == "chat":
            self.display_chat(data.get("sender", "?"), data.get("text", ""))

        elif msg_type == "reveal_result":                                   # Wenn eine Karte umgedreht wurde wird sich  der entsprechende Index geholt und geprüft ob idx ein gültiger Wert ist
            idx = data.get("data", {}).get("index")
            player = message.get("player")
            if idx is not None:
                self.revealed[idx] = True
            self.update_gui()

        elif msg_type == "card_drawn":                             # Wenn neue Karte gezogem wird dann wird diese Karte der Hand übergeben
            card = data.get("card")
            if card is not None:
                self.hand.append(card)
            self.update_gui()

        elif msg_type == "turn":
            current = data.get("player")
            self.is_my_turn = (str(current) == str(self.player_id))
            self.draw_count = 0
            if self.is_my_turn:
                self.status_label.config(text="Du bist am Zug!")
            else:
                self.status_label.config(text=f"{data.get('name', '?')} ist am Zug")
            self.update_gui()

        elif msg_type == "deck_update":
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

        elif msg_type == "game_over":
            # Berechne die finale Punktzahl
            if not all(self.revealed):
                round_score = sum(val for val in self.hand if val != 13)
                self.score_overall += round_score
            
            # Punktzahlen vom Server abrufen
            final_scores = data.get("final_scores", {})
            print(f"[DEBUG] Empfangene Punktzahlen: {final_scores}")
            
            # Rangliste anzeigen und auf Schließen warten
            self.zeige_rangliste(final_scores)
            self.root.after(5000, self.close_connection)

        elif msg_type == "100Pointz":
            print("Spiel wegen 100 Punkten beendet!")
            self.status_label.config(text=f"Spiel beendet - {data.get('player', '?')} hat über 100 Punkte!")
            # Zeige Rangliste mit finalen Punkteständen
            self.zeige_rangliste(data.get("final_scores", {}))
            self.root.after(30000, self.root.destroy)  # Schließe nach 30 Sekunden



    def update_gui(self):
        # Aktualisiert Karten, Stapel, Buttons, Punkteanzeige
        deck_button, discard_pile_button = self.piles
        for i, btn in enumerate(self.card_buttons):
            val = self.hand[i] if self.revealed[i] else "?"
            btn.config(text=val, image=self.images.get(val, self.images["?"]))

            if self.is_my_turn and self.hand is not None and self.points_reached is False:
                btn.config(state=tk.NORMAL)
            else:
                btn.config(state=tk.DISABLED)

            if val == 13:
                btn.config(state=tk.DISABLED)
                btn.config(text="X")                   # Zeigt X an, wenn diese Karte nicht mehr verfügbar ist

        if self.is_my_turn and self.draw_count < 1 and self.start_count > 1:         # Abfrage ob Spieler am Zug ist und ob er schon eine Karte gezogen hat
            deck_button.config(state=tk.NORMAL)
            discard_pile_button.config(state=tk.NORMAL)
        elif self.is_my_turn and self.draw_count >= 1 and self.start_count > 1:  # Abfrage ob Spieler am Zug ist und ob er schon eine Karte gezogen hat
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

    def display_chat(self, sender, message):
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f"{sender}: {message}\n")
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)

    def deck_draw_card(self):
        if not self.is_my_turn:
            self.status_label.config(text="Nicht dein Zug!")
            return
        self.network.send("deck_draw_card")

    def discard_pile_draw(self):
        self.network.send("discard_pile_draw")

    def count_score(self):
        temp = 0
        for i in range(12):
            if self.revealed[i] and self.hand[i] != 13 and self.statusGame:                # Wenn Karte aufgedeckt und nicht 13 (X)
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
        
    def check_for_100P (self):
        if self.score_overall >= 100:
            self.network.send("100P", {"player": self.player_id})
            print("100 Punkte erreicht, spiel vorbei!")
            self.points_reached =  True

    def zeige_rangliste(self, spieler_punkte):
        if not spieler_punkte:
            spieler_punkte = {self.player_id: self.score_overall}
            print("[DEBUG] Keine Punktestände vom Server erhalten, zeige nur eigene Punkte")
        
        rangliste_fenster = tk.Toplevel()
        rangliste_fenster.title("Rangliste")
        rangliste_fenster.geometry("1024x1024")  # Größe auf 1024x1024 angepasst
        rangliste_fenster.resizable(False, False)
        
        try:
            # Bild laden und auf 1024x1024 skalieren
            original_img = Image.open("assets/rangliste.png")
            resized_img = original_img.resize((1024, 1024), Image.Resampling.LANCZOS)
            rangliste_img = ImageTk.PhotoImage(resized_img)
            bg_label = tk.Label(rangliste_fenster, image=rangliste_img)
            bg_label.image = rangliste_img
            bg_label.place(relwidth=1, relheight=1)
            bg_label.lower()
            print("[DEBUG] Rangliste Hintergrundbild geladen und skaliert")
        except Exception as e:
            print(f"[DEBUG] Fehler beim Laden von rangliste.png: {e}")
            print(f"[DEBUG] Aktuelles Verzeichnis: {os.getcwd()}")

        # Frame für die Rangliste
        rang_frame = tk.Frame(rangliste_fenster, bg='white', bd=2, relief='solid')
        rang_frame.place(relx=0.5, rely=0.35, anchor=tk.CENTER)

        # Überschrift
        tk.Label(rang_frame, 
                text="🏆 Finale Rangliste 🏆",
                font=("Arial", 24, "bold"),
                bg='white').pack(pady=15)

        # Die Scores sind bereits sortiert vom Server
        for position, (spieler, punkte) in enumerate(spieler_punkte.items(), 1):
            # Extrahiere den Namen
            name = spieler.split(" als ")[1].rstrip('.') if " als " in spieler else spieler
            
            # Formatierung basierend auf Position
            if position == 1:
                emoji, farbe = "🥇", "gold"
            elif position == 2:
                emoji, farbe = "🥈", "silver"
            elif position == 3:
                emoji, farbe = "🥉", "#CD7F32"
            else:
                emoji, farbe = "👤", "black"

            # Text mit Platzierung, Name und Punkten
            text = f"{emoji} {position}. Platz: {name}\nPunkte: {punkte}"
            
            # Label für Spielereintrag
            tk.Label(rang_frame, 
                    text=text,
                    font=("Arial", 14, "bold" if spieler == self.player_id else "normal"),
                    bg='white',
                    fg=farbe,
                    justify=tk.LEFT).pack(pady=5, padx=15)

        # Schließen Button
        tk.Button(rang_frame,
                  text="Schließen",
                  command=rangliste_fenster.destroy).pack(pady=20)
        
        # Fenster nach 30 Sekunden schließen
        rangliste_fenster.after(30000, rangliste_fenster.destroy)

        print("[DEBUG] Rangliste wurde erstellt")

    def close_connection(self):
        """Clean up network connection before closing"""
        try:
            if hasattr(self, 'network') and self.network:
                if hasattr(self.network, 'socket') and self.network.socket:
                    self.network.socket.close()
                    print("[DEBUG] Network connection closed")
        except Exception as e:
            print(f"[ERROR] Error closing connection: {e}")
        finally:
            if hasattr(self, 'root') and self.root:
                self.root.destroy()
                print("[DEBUG] GUI closed")

    def calculate_final_score(self):
        """Calculate final score from revealed cards"""
        total_score = 0
        for i in range(len(self.grid)):
            for j in range(len(self.grid[i])):
                if self.grid[i][j] is not None:  # Card is revealed
                    total_score += self.grid[i][j]
        print(f"[DEBUG] Calculated score for {self.player_id}: {total_score}")
        return total_score

    def handle_game_over(self):
        """Handle game over event"""
        final_score = self.calculate_final_score()
        print(f"[DEBUG] Submitting final score: {final_score}")
        
        # Send score to server
        self.network.send("submit_score", {
            "player_id": self.player_id,
            "name": self.player_name,
            "score": final_score
        })

