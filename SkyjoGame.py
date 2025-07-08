import random
from class_player import Player

class SkyjoGame:
    def __init__(self):  # Initialisierung der SkyjoGame-Klasse
        self.players = []             # Liste aller Spieler im Spiel
        self.max_players = 8          # Maximale Anzahl erlaubter Spieler
        self.min_players = 2          # Minimale Anzahl benötigter Spieler
        self.deck = []                # Kartenstapel (verdeckt)
        self.discard_pile = []        # Ablagestapel (aufgedeckt)
        self.current_turn = 0         # Index des Spielers, der gerade am Zug ist
        self.started = False          # Status: ob das Spiel gestartet wurde

    def add_player(self, player: Player):  # Spieler zum Spiel hinzufügen
        if len(self.players) < self.max_players:
            self.players.append(player)
            return True
        return False

    def get_player(self, player_id: str):  # Spieler anhand der ID finden
        for p in self.players:
            if p.id == player_id:
                return p
        return None

    def all_ready(self):  # Prüft, ob alle Spieler als "bereit" markiert sind
        return all(p.is_ready for p in self.players)

    def next_turn(self):  # Wechselt zum nächsten Spieler im Rundlauf
        self.current_turn = (self.current_turn + 1) % len(self.players)
        print(f"[DEBUG][SkyjoGame] next_turn: current_turn={self.current_turn}, player_id={self.players[self.current_turn].id}")

    def get_current_player(self):  # Gibt den aktuell aktiven Spieler zurück
        return self.players[self.current_turn] if self.players else None

    def reset_game(self):  # Setzt das Spiel zurück (z. B. nach einer Runde)
        for p in self.players:
            p.reset()  # Spieler zurücksetzen (z. B. Handkarten, Punkte)
        self.deck = []  # Kartenstapel leeren
        self.discard_pile = []  # Ablagestapel leeren
        self.current_turn = 0  # Startspieler zurücksetzen
        self.started = False  # Spielstatus zurücksetzen

    def initialize_deck(self):  # Erstellt und mischt den Kartenstapel
        self.deck = [-2] * 5 + [0] * 5 + list(range(-1, 13)) * 10  # Kartenzusammensetzung
        random.shuffle(self.deck)  # Kartenstapel mischen

    def deal_initial_cards(self):  # Startverteilung der Karten an alle Spieler
        for player in self.players:
            player.hand = self.draw_cards(12)  # Jeder Spieler bekommt 12 Karten
        self.discard_pile.append(self.deck.pop())  # Erste Karte auf den Ablagestapel legen

    def draw_cards(self, amount):  # Zieht mehrere Karten vom Deck
        return [self.deck.pop() for _ in range(amount) if self.deck]

    def draw_new_card(self):  # Zieht eine neue Karte vom Deck (erste Karte)
        if self.deck:
            return self.deck.pop(0)

    def player_ready(self, player: Player):  # Markiert Spieler als bereit & startet ggf. Spiel
        player.is_ready = True
        if self.all_ready():
            self.started = True
            self.initialize_deck()
            self.deal_initial_cards()
            self.discard_pile.append(self.deck.pop())  # Noch eine Karte auf Ablagestapel legen

    def to_dict(self):  # Gibt Spielstatus als Dictionary zurück (für Serialisierung)
        return {
            "players": [p.to_dict() for p in self.players],
            "deck_count": len(self.deck),
            "discard_top": self.discard_pile[-1] if self.discard_pile else None,
            "current_turn": self.players[self.current_turn].id if self.players else None,
            "started": self.started
        }

    def wait_for_communication(self):  # Placeholder für zukünftige Erweiterung (nicht verwendet)
        pass

    def sort_players(self):  # Sortiert Spieler nach Punktestand (absteigend)
        n = len(self.players)
        for i in range(n):
            for j in range(0, n - i - 1):
                if self.players[j].score < self.players[j + 1].score:
                    # Tauscht Spieler, wenn rechter mehr Punkte hat als linker
                    self.players[j], self.players[j + 1] = self.players[j + 1], self.players[j]

    def threeSome(self, hand):  # Prüft, ob ein Dreier (gleiche Karte in einer Spalte) vorliegt
        for i in range(3):  # Es gibt 3 Spalten (Index 0 bis 2)
            if (hand[i] == hand[i + 4] and hand[i] == hand[i + 8] and hand[i] is not None):
                return i  # Gibt Spaltenindex zurück, wenn ein Dreier gefunden wurde
            else:
                return 1234  # Rückgabe, wenn kein Dreier gefunden wurde (unklares Verhalten)

    def check_for_end(self, player: Player):  # Prüft, ob Spieler alle Karten aufgedeckt hat
        if player.all_cards_revealed():
            return True
        return False

