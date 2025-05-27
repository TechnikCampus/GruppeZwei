class Player:
    def __init__(self, player_id: str, avatar: str = None):
        self.id = player_id
        self.hand = []
        self.grid = [[None for _ in range(4)] for _ in range(3)]
        self.revealed = [[False for _ in range(4)] for _ in range(3)]
        self.score = 0
        self.avatar = avatar
        self.is_ready = False
        self.is_connected = True

    def set_card(self, row: int, col: int, card: str):
        self.grid[row][col] = card

    def get_card(self, row: int, col: int):
        return self.grid[row][col]

    def reveal_card(self, row: int, col: int):
        if self.revealed[row][col]:
            return None
        self.revealed[row][col] = True
        return self.grid[row][col]

    def is_card_revealed(self, row: int, col: int):
        return self.revealed[row][col]

    def all_cards_revealed(self):
        return all(all(row) for row in self.revealed)

    def calculate_score(self):
        for i in range(3):
            for j in range(4):
                if self.revealed[i][j] and self.grid[i][j] is not None:
                    try:
                        score += int(self.grid[i][j])
                    except ValueError:
                        continue
        self.score = score
        return score

    def reset(self):
        self.grid = [[None for _ in range(4)] for _ in range(3)]
        self.revealed = [[False for _ in range(4)] for _ in range(3)]
        self.score = 0
        self.hand.clear()
        self.is_ready = False

    def to_dict(self):
        return {
            "id": self.id,
            "grid": self.grid,
            "revealed": self.revealed,
            "score": self.score,
            "avatar": self.avatar,
            "is_ready": self.is_ready,
            "is_connected": self.is_connected,
            "hand": self.hand
        }
