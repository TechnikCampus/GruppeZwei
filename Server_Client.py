# ==== Module & Abhängigkeiten ====
import socket
import threading
import json
from SkyjoGame import SkyjoGame  # Spiellogik
from class_player import Player  # Spielerklasse
from networkClientClass import NetworkClient  # Netzwerk-Client (Client-Seite)
import time

# ==== Konfiguration & Spielstatus ====
PORT = 65435  # Port des Servers

spielerdaten = {}  # Speichert zu jedem Spieler: Verbindung, Name, Spielerobjekt
letzte_aktion = {}  # Merkt sich, ob Spieler in dieser Runde schon etwas getan hat
spiel_lock = threading.Lock()  # Für Thread-Synchronisation
SkyjoSpiel = SkyjoGame()  # Initialisiere das Skyjo-Spielobjekt

config = {
    "anzahl_spieler": 1,  # Anzahl der Spieler
    "anzahl_runden": 1    # Anzahl der Spielrunden
}

switching_cards = False  # Wird true, wenn ein Spieler eine Karte tauscht
turns_left = 0  # Wie viele Spieler müssen noch handeln nach Rundenschluss?
roundisOver = False  # Ob die aktuelle Runde beendet wurde
rounds = 0  # Anzahl verbleibender Runden
finishingPlayer = 9  # Spieler, der die Runde beendet hat

# ==== Nachricht an alle Clients senden ====
def broadcast(message, exclude=None):
    raw = json.dumps(message).encode("utf-8") + b"\n"
    with spiel_lock:
        for sid, daten in spielerdaten.items():
            if exclude is not None and sid == exclude:
                continue
            try:
                daten["conn"].sendall(raw)
            except:
                continue

# ==== Spielrunde starten ====
def spiel_starten():
    global letzte_aktion

    for runde in range(config["anzahl_runden"]):
        SkyjoSpiel.reset_game()
        SkyjoSpiel.initialize_deck()

        with spiel_lock:
            SkyjoSpiel.players.clear()
            for sid in spielerdaten:
                spieler = Player(str(sid))  # Spielerobjekt erzeugen
                spielerdaten[sid]["spieler"] = spieler
                SkyjoSpiel.add_player(spieler)  # Spieler dem Spiel hinzufügen

        SkyjoSpiel.deal_initial_cards()  # Karten verteilen

        # Starte das Spiel für jeden Spieler
        for sid in spielerdaten:
            hand = spielerdaten[sid]["spieler"].hand
            spielerdaten[sid]["conn"].sendall(json.dumps({
                "type": "start",
                "player_id": sid,
                "hand": hand,
                "discard_pile": SkyjoSpiel.discard_pile,
            }).encode("utf-8") + b"\n")

        letzte_aktion = {str(sid): False for sid in spielerdaten}  # Reset Aktionstracker
        for k in list(letzte_aktion.keys()):
            if isinstance(k, int):
                del letzte_aktion[k]

        SkyjoSpiel.started = True
        print("[SERVER] Spielrunde gestartet.")

        # Der erste Spieler ist am Zug
        broadcast({
            "type": "turn",
            "player": SkyjoSpiel.get_current_player().id
        })

# ==== Server-Thread für jeden Client ====
def client_thread(conn, sid):
    global switching_cards, turns_left, roundisOver, rounds, finishingPlayer
    print(f"[SERVER] Spieler {sid} verbunden.")

    buffer = b""
    try:
        while True:
            chunk = conn.recv(4096)
            if not chunk:
                break
            buffer += chunk
            while b"\n" in buffer:
                raw, buffer = buffer.split(b"\n", 1)
                try:
                    daten = json.loads(raw.decode("utf-8"))
                    typ = daten.get("type")
                    data = daten.get("data", {})

                    # ==== Spieler tritt bei ====
                    if typ == "join":
                        print(f"[SERVER] Spieler {sid} beigetreten als {data.get('name', 'Spieler')}.")
                        spielerdaten[sid]["name"] = data.get("name", f"Spieler{sid}")
                        if len(spielerdaten) == config["anzahl_spieler"]:
                            threading.Thread(target=spiel_starten, daemon=True).start()

                    # ==== Karte aufdecken ====
                    elif (typ == "reveal_card"):
                        current_player = SkyjoSpiel.get_current_player()

                        # Wenn Runde vorbei ist, aber nicht alle durch
                        if roundisOver and (len(spielerdaten) == 1 or SkyjoSpiel.get_current_player().id != finishingPlayer):

                            turns_left -= 1
                            if turns_left <= 0:
                                print("[SERVER] no mor rounds left")
                                if rounds <= 0:
                                    # Spiel vorbei
                                    broadcast({"type": "game_over"})
                                    time.sleep(5)
                                    with spiel_lock:
                                        spielerdaten.clear()
                                    roundisOver = False
                                    turns_left = 0
                                    rounds = 0
                                    break
                                else:
                                    # Nächste Runde vorbereiten
                                    turns_left = config["anzahl_spieler"]
                                    print(f"[SERVER] Runde {config['anzahl_runden'] - rounds} beendet. Nächste Runde beginnt.")
                                    SkyjoSpiel.reset_game()
                                    SkyjoSpiel.initialize_deck()
                                    SkyjoSpiel.players.clear()
                                    for sid in spielerdaten:
                                        spieler = Player(str(sid))
                                        spielerdaten[sid]["spieler"] = spieler
                                        SkyjoSpiel.add_player(spieler)
                                    SkyjoSpiel.deal_initial_cards()
                                    for sid in spielerdaten:
                                        hand = spielerdaten[sid]["spieler"].hand
                                        spielerdaten[sid]["conn"].sendall(json.dumps({
                                            "type": "new_round",
                                            "player_id": sid,
                                            "hand": hand,
                                            "discard_pile": SkyjoSpiel.discard_pile,
                                        }).encode("utf-8") + b"\n")
                                    roundisOver = False
                                    finishingPlayer = 9

                        if current_player is None or current_player.id != str(sid):
                            print(f"[SERVER] Spieler {sid} ist NICHT am Zug – Aktion ignoriert.")
                            continue

                        # Spieler hat bereits aufgedeckt
                        if letzte_aktion.get(str(sid), False):
                            print(f"[SERVER] Spieler {sid} hat in diesem Zug bereits eine Karte aufgedeckt.")
                            continue

                        index = data["data"].get("index", 0)
                        i = index // 4
                        j = index % 4
                        spieler = spielerdaten[sid]["spieler"]

                        # ==== Karten tauschen ====
                        if switching_cards:
                            switching_cards = False
                            temp = spieler.hand[index]
                            spieler.hand[index] = SkyjoSpiel.discard_pile.pop()
                            SkyjoSpiel.discard_pile.append(temp)

                            broadcast({
                                "type": "deck_drawn_card",
                                "card": temp
                            })

                            if not spieler.is_card_revealed(i, j):
                                wert = spieler.reveal_card(i, j)

                            conn.sendall(json.dumps({
                                "type": "deck_switched_card",
                                "hand": spieler.hand,
                                "index": index
                            }).encode("utf-8") + b"\n")

                            print(f"[DEGUGG] Index: {index}")

                            SkyjoSpiel.next_turn()
                            next_id = SkyjoSpiel.get_current_player().id
                            for k in letzte_aktion:
                                letzte_aktion[k] = True
                            letzte_aktion[str(next_id)] = False

                            broadcast({
                                "type": "turn",
                                "player": str(next_id),
                                "name": spielerdaten[sid]["name"]
                            })

                            # Dreierprüfung in Spalten
                            for i in range(4):
                                idx1 = i
                                idx2 = i + 4
                                idx3 = i + 8
                                if (
                                    spieler.hand[idx1] == spieler.hand[idx2] == spieler.hand[idx3] and spieler.hand[idx1] != 13
                                ):
                                    print(f"Dreier gefunden in Spalte {i}")

                                    SkyjoSpiel.discard_pile.append(spieler.hand[idx1])
                                    SkyjoSpiel.discard_pile.append(spieler.hand[idx2])
                                    SkyjoSpiel.discard_pile.append(spieler.hand[idx3])

                                    temp = spieler.hand[idx1]

                                    spieler.hand[idx1] = 13
                                    spieler.hand[idx2] = 13
                                    spieler.hand[idx3] = 13

                                    conn.sendall(json.dumps({
                                        "type": "threesome",
                                        "hand": spieler.hand
                                    }).encode("utf-8") + b"\n")

                                    conn.sendall(json.dumps({
                                        "type": "deck_drawn_card",
                                        "card": temp
                                    }).encode("utf-8") + b"\n")

                        # ==== Karte einfach aufdecken ====
                        else:
                            if not spieler.is_card_revealed(i, j):
                                wert = spieler.reveal_card(i, j)
                                print(f"[SERVER] Spieler {sid} deckt Karte {i},{j} = {wert} auf")

                                letzte_aktion[str(sid)] = True

                                broadcast({
                                    "type": "reveal_result",
                                    "data": {"index": i * 4 + j},
                                    "player": sid
                                })

                                SkyjoSpiel.next_turn()
                                next_id = SkyjoSpiel.get_current_player().id
                                print(f"[DEBUG] Nächster Spieler ist: {next_id}")
                                for k in letzte_aktion:
                                    letzte_aktion[k] = True
                                letzte_aktion[str(next_id)] = False
                                print(f"[DEBUG] letzte_aktion nach Spielerwechsel: {letzte_aktion}")
                                broadcast({
                                    "type": "turn",
                                    "player": str(next_id),
                                    "name": spielerdaten[sid]["name"]
                                })

                            # Dreierprüfung erneut
                            for i in range(4):
                                idx1 = i
                                idx2 = i + 4
                                idx3 = i + 8
                                if (
                                    spieler.hand[idx1] == spieler.hand[idx2] == spieler.hand[idx3] and spieler.hand[idx1] != 13
                                ):
                                    print(f"Dreier gefunden in Spalte {i}")

                                    SkyjoSpiel.discard_pile.append(spieler.hand[idx1])
                                    SkyjoSpiel.discard_pile.append(spieler.hand[idx2])
                                    SkyjoSpiel.discard_pile.append(spieler.hand[idx3])

                                    temp = spieler.hand[idx1]

                                    spieler.hand[idx1] = 13
                                    spieler.hand[idx2] = 13
                                    spieler.hand[idx3] = 13

                                    conn.sendall(json.dumps({
                                        "type": "threesome",
                                        "hand": spieler.hand
                                    }).encode("utf-8") + b"\n")

                                    conn.sendall(json.dumps({
                                        "type": "deck_drawn_card",
                                        "card": temp
                                    }).encode("utf-8") + b"\n")

                    # ==== Chatnachricht senden ====
                    elif typ == "chat":
                        broadcast({
                            "type": "chat",
                            "sender": spielerdaten[sid]["name"],
                            "text": data.get("text", "")
                        })

                    # ==== Karte vom Deck ziehen ====
                    elif typ == "deck_draw_card":
                        neue_karte = SkyjoSpiel.draw_new_card() if SkyjoSpiel.deck else None
                        if neue_karte:
                            SkyjoSpiel.discard_pile.append(neue_karte)
                            conn.sendall(json.dumps({
                                "type": "deck_drawn_card",
                                "card": neue_karte
                            }).encode("utf-8") + b"\n")
                            broadcast({
                                "type": "deck_update",
                                "deck_count": len(SkyjoSpiel.deck),
                                "card": neue_karte
                            })

                    # ==== Karte vom Ablagestapel ziehen (für Tausch) ====
                    elif typ == "discard_pile_draw":
                        switching_cards = True

                    # ==== Spieler beendet Runde ====
                    elif typ == "round_over":
                        spieler = data.get("player", "?")
                        print(f"{spieler} hat die Runde beendet")
                        turns_left = len(spielerdaten) - 1
                        if roundisOver is not True:
                            rounds -= 1
                        roundisOver = True
                        finishingPlayer = spieler
                        
                        if turns_left <= 0:
                            roundisOver = True

                except json.JSONDecodeError:
                    print("[SERVER] Ungültige Nachricht erhalten.")
    except:
        print(f"[SERVER] Spieler {sid} getrennt.")
    finally:
        with spiel_lock:
            if sid in spielerdaten:
                del spielerdaten[sid]
        conn.close()

# ==== Serverstart ====
def server_starten(konfig):
    global config, turns_left, rounds
    config = konfig

    turns_left = config["anzahl_spieler"]
    rounds = config["anzahl_runden"]

    SkyjoSpiel.reset_game()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", PORT))
    server.listen(10)
    print(f"[SERVER] Skyjo-Server gestartet auf Port {PORT}")

    sid = 0
    while True:
        conn, addr = server.accept()
        with spiel_lock:
            if len(spielerdaten) >= config["anzahl_spieler"]:
                conn.close()
                continue
            spielerdaten[sid] = {"conn": conn}
        threading.Thread(target=client_thread, args=(conn, sid), daemon=True).start()
        sid += 1


# ==== Verbesserte keyboard_input.py ====
# Behandelt Tasteneingaben für die GUI (z. B. Karten auswählen, tauschen etc.)
import tkinter as tk
from tkinter import messagebox

class KeyboardInputHandler:
    def __init__(self, root, network_client, card_buttons):
        self.root = root
        self.network = network_client
        self.card_buttons = card_buttons  # Referenz auf die 3x4 Button-Matrix für die Karten
        self.selected_row = 0  # Aktuell ausgewählte Zeile (für Steuerung mit Pfeiltasten)
        self.selected_col = 0  # Aktuell ausgewählte Spalte

        # Tastaturbelegung (Key Bindings)
        root.bind("<KeyPress-z>", self.draw_card)        # Z = Karte vom Deck ziehen
        root.bind("<KeyPress-a>", self.discard_card)     # A = Karte ablegen
        root.bind("<KeyPress-t>", self.swap_card)        # T = Karte tauschen
        root.bind("<KeyPress-w>", self.pass_card)        # W = weitergeben (nicht aktiv?)
        root.bind("<KeyPress-r>", self.set_ready)        # R = bereit
        root.bind("<KeyPress-e>", self.show_cards)       # E = Karten anzeigen
        root.bind("<Left>", self.move_left)              # Pfeil links = Auswahl bewegen
        root.bind("<Right>", self.move_right)            # Pfeil rechts
        root.bind("<Up>", self.move_up)                  # Pfeil oben
        root.bind("<Down>", self.move_down)              # Pfeil unten
        root.bind("<Return>", self.reveal_card)          # ENTER = Karte aufdecken
        root.bind("<Escape>", self.cancel_action)        # ESC = Aktion abbrechen
        root.bind("<KeyPress-h>", self.show_help)        # H = Hilfe anzeigen
        root.bind("<KeyPress-q>", self.quit_game)        # Q = Spiel verlassen

        self.update_selection_highlight()  # Visuelle Markierung der Auswahl

    def send(self, msg_type, data=None):
        # Sendet Nachricht an Server, wenn Netzwerkverbindung aktiv ist
        if self.network and self.network.is_connected():
            self.network.send(msg_type, data or {})

    # ==== Steuerfunktionen ====
    def draw_card(self, event=None): self.send("draw_card")
    def discard_card(self, event=None): self.send("discard_card", {"row": self.selected_row, "col": self.selected_col})
    def swap_card(self, event=None): self.send("swap_card", {"row": self.selected_row, "col": self.selected_col})
    def pass_card(self, event=None): self.send("pass_card")
    def set_ready(self, event=None): self.send("ready")
    def show_cards(self, event=None): self.send("show_cards")
    def reveal_card(self, event=None): self.send("reveal_card", {"row": self.selected_row, "col": self.selected_col})
    def cancel_action(self, event=None): self.send("cancel_action")
    def quit_game(self, event=None): self.send("quit"); self.root.quit()

    # ==== Bewegung mit Pfeiltasten ====
    def move_left(self, event=None): self.selected_col = (self.selected_col - 1) % 4; self.update_selection_highlight()
    def move_right(self, event=None): self.selected_col = (self.selected_col + 1) % 4; self.update_selection_highlight()
    def move_up(self, event=None): self.selected_row = (self.selected_row - 1) % 3; self.update_selection_highlight()
    def move_down(self, event=None): self.selected_row = (self.selected_row + 1) % 3; self.update_selection_highlight()

    def update_selection_highlight(self):
        # Hebt die ausgewählte Karte visuell hervor
        for i in range(3):
            for j in range(4):
                btn = self.card_buttons[i][j]
                if i == self.selected_row and j == self.selected_col:
                    btn.config(relief=tk.SOLID, borderwidth=3)
                else:
                    btn.config(relief=tk.RAISED, borderwidth=1)

    def show_help(self, event=None):
        # Zeigt Hilfe-Fenster mit Tastenkombinationen
        messagebox.showinfo("Hilfe", "Tastenkürzel:\nZ=ziehen\nA=ablegen\nT=tauschen\nW=weitergeben\nR=bereit\nE=zeigen\nEnter=aufdecken\nEsc=abbrechen\nQ=beenden")



# ==== Haupt-GUI für den Client ====
class GameGUI:
    def __init__(self, root, server_ip="127.0.0.1", server_port=5000):
        self.root = root
        self.root.title("Skyjo Client")  # Titel des Fensters
        self.network = NetworkClient(server_ip, server_port, self.handle_server_message)  # Netzwerkverbindung zum Server

        self.player = None               # Spieler-ID (eigener Spieler)
        self.current_player = None      # Wer ist aktuell dran?

        # 3x4 Karten-Buttons für die Hand (12 Karten)
        self.card_buttons = [[None for _ in range(4)] for _ in range(3)]

        # GUI-Komponenten für Chat und Statusanzeige
        self.chat_entry = tk.Entry(root, width=40)  # Texteingabefeld für Chat
        self.chat_button = tk.Button(root, text="Senden", command=self.send_chat_message)  # Sendebutton
        self.chat_display = tk.Text(root, height=10, width=60, state=tk.DISABLED)  # Chatverlauf
        self.status_label = tk.Label(root, text="Status")  # Statusanzeige (z.B. wer ist dran)
        self.timer_label = tk.Label(root, text="Zug-Timer: -")  # Optionaler Timer

        self.timer_active = False  # Steuerung für Timer (falls aktiviert)

        self.build_gui()  # Erzeugt das Fensterlayout (Buttons, Labels, etc.)

        # Tastatursteuerung aktivieren
        self.keyboard_handler = KeyboardInputHandler(self.root, self.network, self.card_buttons)

        self.prompt_player_name()  # Fragt den Namen des Spielers ab
        self.root.after(100, self.connect_to_server)  # Verbindungsversuch nach kurzer Verzögerung
