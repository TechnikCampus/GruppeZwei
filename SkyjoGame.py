import random
from class_player import Player


class SkyjoGame:
    def __init__(self):
        self.players = []
        self.max_players = 4
        self.deck = []
        self.discard_pile = []
        self.current_turn = 0
        self.started = False

    def add_player(self, player: Player):
        if len(self.players) < self.max_players:
            self.players.append(player)
            return True
        return False

    def get_player(self, player_id: str):
        for p in self.players:
            if p.id == player_id:
                return p
        return None

    def all_ready(self):
        return all(p.is_ready for p in self.players)

    def next_turn(self):
        self.current_turn = (self.current_turn + 1) % len(self.players)

    def get_current_player(self):
        return self.players[self.current_turn] if self.players else None

    def reset_game(self):
        for p in self.players:
            p.reset()
        self.deck = []
        self.discard_pile = []
        self.current_turn = 0
        self.started = False

    def initialize_deck(self):
        self.deck = [-2] * 5 + list(range(0, 13)) * 10
        random.shuffle(self.deck)

    def deal_initial_cards(self):
        for player in self.players:
            player.hand = self.draw_cards(12)

    def draw_cards(self, amount):
        return [self.deck.pop() for _ in range(amount) if self.deck]

    def player_draw_card(self, player: Player):
        if self.started and player == self.get_current_player():
            if self.deck:
                card = self.deck.pop()
                player.hand.append(card)
                return card
        return None

    def player_discard_card(self, player: Player, card: str):
        if card in player.hand:
            player.hand.remove(card)
            self.discard_pile.append(card)
            return True
        return False

    def player_ready(self, player: Player):
        player.is_ready = True
        if self.all_ready():
            self.started = True
            self.initialize_deck()
            self.deal_initial_cards()

    def to_dict(self):
        return {
            "players": [p.to_dict() for p in self.players],
            "deck_count": len(self.deck),
            "discard_top": self.discard_pile[-1] if self.discard_pile else None,
            "current_turn": self.players[self.current_turn].id if self.players else None,
            "started": self.started
        }
