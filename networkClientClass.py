import socket
import threading
import json


class NetworkClient:
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
