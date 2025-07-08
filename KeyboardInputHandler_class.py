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
