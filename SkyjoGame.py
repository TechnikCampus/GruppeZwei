import random
from class_player import Player


class SkyjoGame:
    def __init__(self):             # initialisierung der SkyjoGame-Klasse
        self.players = []
        self.max_players = 8    # Maximale Anzahl der Spieler
        self.min_players = 2    # Minimale Anzahl der Spieler
        self.deck = []          # Kartenstapel (umgedreht)
        self.discard_pile = []  # Ablagestapel (aufgedeckt)
        self.current_turn = 0   # Index des aktuellen Spielers
        self.started = False    # Spiel gestartet oder nicht

    def add_player(self, player: Player):   # Spieler hinzufügen
        if len(self.players) < self.max_players:
            self.players.append(player)
            return True
        return False

    def get_player(self, player_id: str):   # Spieler anhand der ID finden
        for p in self.players:
            if p.id == player_id:
                return p
        return None

    def all_ready(self):        # Überprüfen, ob alle Spieler bereit sind
        return all(p.is_ready for p in self.players)

    def next_turn(self):        # Nächster Spieler am Zug
        self.current_turn = (self.current_turn + 1) % len(self.players)
        print(f"[DEBUG][SkyjoGame] next_turn: current_turn={self.current_turn}, player_id={self.players[self.current_turn].id}")

    def get_current_player(self):   	    # Aktuellen Spieler zurückgeben
        return self.players[self.current_turn] if self.players else None

    def reset_game(self):               # Spiel zurücksetzen
        for p in self.players:
            p.reset()
        self.deck = []
        self.discard_pile = []
        self.current_turn = 0
        self.started = False

    def initialize_deck(self):      # Kartenstapel initialisieren
        self.deck = [-2] * 5 + [0] * 5 + list(range(-1, 13)) * 10
        random.shuffle(self.deck)

    def deal_initial_cards(self):
        for player in self.players:
            player.hand = self.draw_cards(12)
        self.discard_pile.append(self.deck.pop())

    def draw_cards(self, amount):
        return [self.deck.pop() for _ in range(amount) if self.deck]

    def draw_new_card(self):
        if self.deck:
            # card = self.deck.pop()
            # player.hand.append(card)
            # return card
            return self.deck.pop(0)

    def player_ready(self, player: Player):
        player.is_ready = True
        if self.all_ready():
            self.started = True
            self.initialize_deck()
            self.deal_initial_cards()
            self.discard_pile.append(self.deck.pop())

    def to_dict(self):
        return {
            "players": [p.to_dict() for p in self.players],
            "deck_count": len(self.deck),
            "discard_top": self.discard_pile[-1] if self.discard_pile else None,
            "current_turn": self.players[self.current_turn].id if self.players else None,
            "started": self.started
        }

    def wait_for_communication(self):
        pass

    def sort_players(self):
        n = len(self.players)
        for i in range(n):
            for j in range(0, n - i - 1):
                if self.players[j].score < self.players[j + 1].score:
                    # Tausche die Objekte, wenn der linke Score kleiner ist
                    self.players[j], self.players[j + 1] = self.players[j + 1], self.players[j]

    def threeSome(self, hand):
        for i in range(3):
            if (hand[i] == hand[i + 4] and hand[i] == hand[i + 8] and hand[i] is not None):
                return i
            else:
                return 1234

    def check_for_end(self, player: Player):
        if player.all_cards_revealed():
            return True
        return False
