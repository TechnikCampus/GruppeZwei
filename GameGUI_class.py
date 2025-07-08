
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
