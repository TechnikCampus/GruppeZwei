import socket
import threading
import json
from SkyjoGame import SkyjoGame
from class_player import Player

# ==== Konfiguration & Spielstatus ====
PORT = 65435
switching_cards = False


class NetworkClient:                                                            #Anmerkung: Klasse als eigene Datei machen
    def __init__(self, server_ip, server_port, on_message, on_connected=None):
        self.server_ip = server_ip
        self.server_port = server_port
        self.on_message = on_message
        self.on_connected = on_connected
        self.sock = None
        self.running = False
        self.buffer = b""

    def connect(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.server_ip, self.server_port))
            self.running = True
            threading.Thread(target=self._receive_loop, daemon=True).start()
            if self.on_connected:
                self.on_connected()
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


spielerdaten = {}
letzte_aktion = {}
spiel_lock = threading.Lock()
SkyjoSpiel = SkyjoGame()

config = {
    "anzahl_spieler": 2,
    "anzahl_runden": 1
}


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


# ==== Spiellogik ====
def spiel_starten():
    global letzte_aktion

    for runde in range(config["anzahl_runden"]):
        SkyjoSpiel.reset_game()
        SkyjoSpiel.initialize_deck()

        with spiel_lock:
            SkyjoSpiel.players.clear()
            for sid in spielerdaten:
                spieler = Player(str(sid))
                spielerdaten[sid]["spieler"] = spieler
                SkyjoSpiel.add_player(spieler)

        SkyjoSpiel.deal_initial_cards()

        for sid in spielerdaten:
            hand = spielerdaten[sid]["spieler"].hand
            spielerdaten[sid]["conn"].sendall(json.dumps({
                "type": "start",
                "player_id": sid,
                "hand": hand,
                "discard_pile": SkyjoSpiel.discard_pile,

            }).encode("utf-8") + b"\n")

        letzte_aktion = {str(sid): False for sid in spielerdaten}   # Reset letzte Aktion für alle Spieler
        # Entferne alle int-Keys, falls noch vorhanden
        for k in list(letzte_aktion.keys()):
            if isinstance(k, int):
                del letzte_aktion[k]

        SkyjoSpiel.started = True
        print("[SERVER] Spielrunde gestartet.")

        # Ersten Spieler benachrichtigen
        broadcast({
            "type": "turn",
            "player": SkyjoSpiel.get_current_player().id
        })


# ==== Server-Thread pro Client ====
def client_thread(conn, sid):
    global switching_cards
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

                    if typ == "join":
                        print(f"[SERVER] Spieler {sid} beigetreten als {data.get('name', 'Spieler')}.")
                        spielerdaten[sid]["name"] = data.get("name", f"Spieler{sid}")
                        if len(spielerdaten) == config["anzahl_spieler"]:
                            threading.Thread(target=spiel_starten, daemon=True).start()

                    elif (typ == "reveal_card"):
                        current_player = SkyjoSpiel.get_current_player()
                        print(f"[DEBUG] Aktueller Spieler laut Server: {current_player.id if current_player else 'None'} | Aktuell anfragender: {sid}")
                        print(f"[DEBUG] letzte_aktion vor Prüfung: {letzte_aktion}")
                        if current_player is None or current_player.id != str(sid):
                            print(f"[SERVER] Spieler {sid} ist NICHT am Zug – Aktion ignoriert.")
                            continue

                        # Nur eine Aktion pro Zug erlauben
                        if letzte_aktion.get(str(sid), False):
                            print(f"[SERVER] Spieler {sid} hat in diesem Zug bereits eine Karte aufgedeckt.")
                            continue

                        index = data["data"].get("index", 0)
                        i = index // 4
                        j = index % 4
                        spieler = spielerdaten[sid]["spieler"]

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
                            print(f"[DEBUG] letzte_aktion nach Spielerwechsel: {letzte_aktion}")
                            broadcast({
                                "type": "turn",
                                "player": str(next_id),
                                "name": spielerdaten[sid]["name"]
                            })

                            for i in range(4):  # 3 Zeilen
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

                        else:

                            if not spieler.is_card_revealed(i, j):
                                wert = spieler.reveal_card(i, j)
                                print(f"[SERVER] Spieler {sid} deckt Karte {i},{j} = {wert} auf")

                                # Merke: Spieler hat in diesem Zug bereits gehandelt
                                letzte_aktion[str(sid)] = True
                                print(f"[DEBUG] letzte_aktion nach Aufdecken: {letzte_aktion} \n")

                                # Nachricht an alle Clients
                                broadcast({
                                    "type": "reveal_result",
                                    "data": {"index": i * 4 + j},
                                    "player": sid
                                })

                                # if SkyjoSpiel.check_for_end(spieler):
                                    # print(f"[SERVER] Spieler {sid} hat alle Karten aufgedeckt – Spielende.")
                                    # broadcast({
                                    #     "type": "game_over",
                                    #     "winner": sid
                                    # })
                                # else:
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

                            for i in range(4):  # 3 Zeilen
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

                    elif typ == "chat":
                        broadcast({
                            "type": "chat",
                            "sender": spielerdaten[sid]["name"],
                            "text": data.get("text", "")
                        })

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

                    elif typ == "discard_pile_draw":
                        switching_cards = True

                except json.JSONDecodeError:
                    print("[SERVER] Ungültige Nachricht erhalten.")
    except:
        print(f"[SERVER] Spieler {sid} getrennt.")
    finally:
        with spiel_lock:
            if sid in spielerdaten:
                del spielerdaten[sid]
        conn.close()


# ==== Haupt-Serverfunktion ====
def server_starten(konfig):
    print("[DEBUG] server_starten() wurde aufgerufen")
    global config
    config = konfig

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


# Verbesserte keyboard_input.py mit GUI-Markierung, Netzwerkverbindung und Event-Unterstützung
import tkinter as tk
from tkinter import messagebox

class KeyboardInputHandler:
    def __init__(self, root, network_client, card_buttons):
        self.root = root
        self.network = network_client
        self.card_buttons = card_buttons  # Referenz auf Button-Matrix (3x4)
        self.selected_row = 0
        self.selected_col = 0

        # Tastenzuweisungen
        root.bind("<KeyPress-z>", self.draw_card)
        root.bind("<KeyPress-a>", self.discard_card)
        root.bind("<KeyPress-t>", self.swap_card)
        root.bind("<KeyPress-w>", self.pass_card)
        root.bind("<KeyPress-r>", self.set_ready)
        root.bind("<KeyPress-e>", self.show_cards)
        root.bind("<Left>", self.move_left)
        root.bind("<Right>", self.move_right)
        root.bind("<Up>", self.move_up)
        root.bind("<Down>", self.move_down)
        root.bind("<Return>", self.reveal_card)
        root.bind("<Escape>", self.cancel_action)
        root.bind("<KeyPress-h>", self.show_help)
        root.bind("<KeyPress-q>", self.quit_game)

        self.update_selection_highlight()

    def send(self, msg_type, data=None):
        if self.network and self.network.is_connected():
            self.network.send(msg_type, data or {})

    def draw_card(self, event=None):
        self.send("draw_card")

    def discard_card(self, event=None):
        self.send("discard_card", {"row": self.selected_row, "col": self.selected_col})

    def swap_card(self, event=None):
        self.send("swap_card", {"row": self.selected_row, "col": self.selected_col})

    def pass_card(self, event=None):
        self.send("pass_card")

    def set_ready(self, event=None):
        self.send("ready")

    def show_cards(self, event=None):
        self.send("show_cards")

    def reveal_card(self, event=None):
        self.send("reveal_card", {"row": self.selected_row, "col": self.selected_col})

    def cancel_action(self, event=None):
        self.send("cancel_action")

    def move_left(self, event=None):
        self.selected_col = (self.selected_col - 1) % 4
        self.update_selection_highlight()

    def move_right(self, event=None):
        self.selected_col = (self.selected_col + 1) % 4
        self.update_selection_highlight()

    def move_up(self, event=None):
        self.selected_row = (self.selected_row - 1) % 3
        self.update_selection_highlight()

    def move_down(self, event=None):
        self.selected_row = (self.selected_row + 1) % 3
        self.update_selection_highlight()

    def update_selection_highlight(self):
        for i in range(3):
            for j in range(4):
                btn = self.card_buttons[i][j]
                if i == self.selected_row and j == self.selected_col:
                    btn.config(relief=tk.SOLID, borderwidth=3)
                else:
                    btn.config(relief=tk.RAISED, borderwidth=1)

    def show_help(self, event=None):
        messagebox.showinfo("Hilfe", "Tastenkürzel:\nZ=ziehen\nA=ablegen\nT=tauschen\nW=weitergeben\nR=bereit\nE=zeigen\nEnter=aufdecken\nEsc=abbrechen\nQ=beenden")

    def quit_game(self, event=None):
        self.send("quit")
        self.root.quit()


# Integration in GameGUI
class GameGUI:
    def __init__(self, root, server_ip="127.0.0.1", server_port=5000):
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
        self.keyboard_handler = KeyboardInputHandler(self.root, self.network, self.card_buttons)  # <--- Integration
        self.prompt_player_name()
        self.root.after(100, self.connect_to_server)