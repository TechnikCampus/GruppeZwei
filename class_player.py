class Player:
    def __init__(self, player_id: str, avatar: str = None):
        self.id = player_id                            # Eindeutige Spieler-ID
        self.hand = []                                 # Kartenhand (z. B. 12 Karten flach gespeichert)
        self.grid = [[None for _ in range(4)] for _ in range(3)]  # 3x4-Kartenraster (optional genutzt)
        self.revealed = [[False for _ in range(4)] for _ in range(3)]  # Welche Karten sind aufgedeckt?
        self.score = 0                                 # Aktueller Rundenscore
        self.score_overall = 0                         # Gesamtscore über mehrere Runden
        self.avatar = avatar                           # Optional: Avatar-Name oder Bild
        self.is_ready = False                          # Ist der Spieler bereit?
        self.is_connected = True                       # Ist der Spieler aktuell verbunden?

    def set_card(self, row: int, col: int, card: str):
        # Setzt eine Karte an eine bestimmte Position im Raster
        self.grid[row][col] = card

    def get_card(self, row: int, col: int):
        # Gibt die Karte an der angegebenen Position zurück
        return self.grid[row][col]

    def reveal_card(self, row: int, col: int):
        # Deckt eine Karte auf, wenn sie noch nicht sichtbar ist
        if self.revealed[row][col]:
            return None
        self.revealed[row][col] = True
        return self.grid[row][col]

    def is_card_revealed(self, row: int, col: int):
        # Prüft, ob die Karte an der Position bereits aufgedeckt wurde
        return self.revealed[row][col]

    def all_cards_revealed(self):
        # Gibt True zurück, wenn alle Karten aufgedeckt sind
        return all(all(row) for row in self.revealed)

    def calculate_score(self):
        # Berechnet den aktuellen Punktestand basierend auf aufgedeckten Karten
        self.score = 0
        for i in range(3):
            for j in range(4):
                if self.revealed[i][j] and self.grid[i][j] is not None:
                    try:
                        self.score += int(self.grid[i][j])  # Karte muss in Zahl konvertierbar sein
                    except ValueError:
                        continue  # Ignoriere nicht-numerische Karten (z. B. Sonderkarten)
        return self.score

    def reset(self):
        # Setzt den Spielerstatus für die nächste Runde zurück
        self.grid = [[None for _ in range(4)] for _ in range(3)]  # Raster zurücksetzen
        self.revealed = [[False for _ in range(4)] for _ in range(3)]  # Sichtbarkeiten zurücksetzen
        self.score_overall += self.score  # Rundenscore zur Gesamtsumme hinzufügen
        self.score = 0
        self.hand.clear()  # Kartenhand leeren
        self.is_ready = False  # Spieler muss sich erneut bereit melden

    def to_dict(self):
        # Gibt alle wichtigen Spielerdaten als Dictionary zurück (für JSON-Übertragung)
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

