import socket
import threading
import json

class NetworkClient:
    def __init__(self, server_ip, server_port, on_message, on_connected=None):
        self.server_ip = server_ip                          # IP-Adresse des Servers
        self.server_port = server_port                      # Port des Servers
        self.on_message = on_message                        # Callback-Funktion für eingehende Nachrichten
        self.on_connected = on_connected                    # Optionaler Callback bei erfolgreicher Verbindung
        self.sock = None                                    # Socket-Objekt für TCP-Verbindung
        self.running = False                                # Gibt an, ob die Verbindung aktiv ist
        self.buffer = b""                                   # Puffer für eingehende Daten (Byteweise empfangen)

    def connect(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Erstelle TCP-Socket
            self.sock.connect((self.server_ip, self.server_port))          # Verbindungsaufbau zum Server
            self.running = True
            threading.Thread(target=self._receive_loop, daemon=True).start()  # Starte Empfangs-Thread
            if self.on_connected:
                self.on_connected()  # Optionaler Callback bei Verbindung
            return True
        except Exception as e:
            print(f"[ERROR] Verbindung fehlgeschlagen: {e}")  # Fehler beim Verbindungsaufbau
            return False

    def send(self, msg_type, data=None):
        if not self.running:
            print("[WARN] Nicht verbunden mit Server")  # Kein Senden möglich, wenn nicht verbunden
            return
        # Erstelle JSON-Nachricht und kodieren mit UTF-8, endet mit Zeilenumbruch zur Trennung
        message = json.dumps({"type": msg_type, "data": data or {}}).encode("utf-8") + b"\n"
        try:
            self.sock.sendall(message)  # Sende Nachricht über TCP
        except Exception as e:
            print(f"[ERROR] Sendefehler: {e}")  # Fehler beim Senden

    def _receive_loop(self):
        # Endlosschleife zum Empfangen von Nachrichten
        while self.running:
            try:
                chunk = self.sock.recv(4096)  # Empfange bis zu 4096 Bytes
                if not chunk:
                    break  # Verbindung wurde vom Server beendet
                self.buffer += chunk  # Hänge empfangene Daten an den Puffer an
                while b"\n" in self.buffer:  # Solange vollständige Nachrichten vorhanden sind
                    raw, self.buffer = self.buffer.split(b"\n", 1)  # Nachricht vom Rest abtrennen
                    try:
                        msg = json.loads(raw.decode("utf-8"))  # JSON-Nachricht dekodieren
                        self.on_message(msg)  # Callback aufrufen und Nachricht übergeben
                    except json.JSONDecodeError:
                        print("[WARN] Ungültige Nachricht erhalten.")  # Nachricht war kein gültiges JSON
            except Exception as e:
                print(f"[ERROR] Empfangsfehler: {e}")  # Netzwerkfehler beim Empfangen
                break

