import socket
import threading
import json
from SkyjoGame import SkyjoGame
from class_player import Player

PORT = 65433
MAX_SPIELER = 4
spiel_lock = threading.Lock()

spiel = SkyjoGame()
spielerdaten = {}  # sid: {"conn": socket, "player": Player}


def broadcast(message, exclude=None):
    raw = json.dumps(message).encode("utf-8") + b"\n"
    with spiel_lock:
        for sid, daten in spielerdaten.items():
            if exclude is not None and sid == exclude:
                continue
            try:
                daten["conn"].sendall(raw)
            except Exception:
                continue


def handle_message(sid, msg):
    typ = msg.get("type")
    data = msg.get("data", {})
    player = spielerdaten[sid]["player"]

    if typ == "join":
        print(f"Spieler {player.id} tritt bei")
        spiel.add_player(player)
        if len(spiel.players) == MAX_SPIELER:
            for p in spiel.players:
                spiel.player_ready(p)
            broadcast({
                "type": "start",
                "data": {
                    "players": [p.to_dict() for p in spiel.players],
                    "discard_top": spiel.discard_pile[-1]
                }
            })

    elif typ == "reveal_card":
        row = data.get("row")
        col = data.get("col")
        if row is not None and col is not None:
            card = player.reveal_card(row, col)
            broadcast({
                "type": "reveal_result",
                "data": {"row": row, "col": col, "card": card},
                "player": player.id
            })

    elif typ == "draw_card":
        if spiel.deck:
            card = spiel.deck.pop()
            player.hand.append(card)
            spiel.discard_pile.append(card)
            daten = {
                "type": "card_drawn",
                "card": card
            }
            spielerdaten[sid]["conn"].sendall(
                json.dumps(daten).encode("utf-8") + b"\n")

    elif typ == "chat":
        broadcast({
            "type": "chat",
            "sender": player.id,
            "text": data.get("text", "")
        })



def client_thread(conn, sid):
    print(f"[INFO] Spieler {sid} verbunden")
    player = Player(str(sid))
    with spiel_lock:
        spielerdaten[sid] = {"conn": conn, "player": player}

    buffer = b""
    try:
        while True:
            chunk = conn.recv(4096)
            if not chunk:
                break
            buffer += chunk
            while b"\n" in buffer:
                raw, buffer = buffer.split(b"\n", 1)
                try:
                    message = json.loads(raw.decode("utf-8"))
                    handle_message(sid, message)
                except json.JSONDecodeError:
                    print("[WARN] Ungültige Nachricht empfangen")
    except Exception as e:
        print(f"[ERROR] Verbindung zu Spieler {sid} verloren: {e}")
    finally:
        with spiel_lock:
            del spielerdaten[sid]
        conn.close()
        print(f"[INFO] Spieler {sid} getrennt")



def server_starten():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", PORT))
    server.listen(MAX_SPIELER)
    print(f"[SERVER] Skyjo-Server läuft auf Port {PORT}")

    sid = 0
    while sid < MAX_SPIELER:
        conn, addr = server.accept()
        threading.Thread(target=client_thread, args=(conn, sid), daemon=True).start()
        sid += 1


if __name__ == "__main__":
    server_starten()
