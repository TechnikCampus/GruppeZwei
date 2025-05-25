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
from keyboard_input import KeyboardInputHandler

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
