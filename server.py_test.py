# server.py
import socket
import threading
import json
import random
import time

PORT = 65433
MAX_SPIELER = 4
KARTEN_PRO_SPIELER = 12
KARTEN_DECK = [-2] * 5 + list(range(0, 13)) * 10
random.shuffle(KARTEN_DECK)

spielerdaten = {}
spiel_lock = threading.Lock()

def karten_ziehen(anzahl):
    return [KARTEN_DECK.pop() for _ in range(anzahl) if KARTEN_DECK]

def broadcast(message, exclude=None):
    raw = json.dumps(message).encode("utf-8") + b"\n"
    with spiel_lock:
        for sid, daten in spielerdaten.items():
            if exclude is not None and sid == exclude:
                continue
            try:
                daten["conn"].sendall(raw)
            except:
                continue

def client_thread(conn, sid):
    print(f"Spieler {sid} verbunden.")
    karten = karten_ziehen(KARTEN_PRO_SPIELER)
    with spiel_lock:
        spielerdaten[sid]["karten"] = karten

    conn.sendall(json.dumps({
        "type": "start",
        "player_id": sid,
        "hand": karten
    }).encode("utf-8") + b"\n")

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
                    daten = json.loads(raw.decode("utf-8"))
                    typ = daten.get("type")
                    if typ == "chat":
                        broadcast({
                            "type": "chat",
                            "sender": daten["data"].get("sender", "?"),
                            "text": daten["data"].get("text", "")
                        })
                    elif typ == "draw_card":
                        neue_karte = karten_ziehen(1)[0] if KARTEN_DECK else None
                        spielerdaten[sid]["karten"].append(neue_karte)
                        conn.sendall(json.dumps({
                            "type": "card_drawn",
                            "card": neue_karte
                        }).encode("utf-8") + b"\n")
                    elif typ == "reveal_card":
                        broadcast({
                            "type": "reveal_result",
                            "data": daten["data"],
                            "player": sid
                        })
                except json.JSONDecodeError:
                    print("Ungültige Nachricht")
    except:
        print(f"Spieler {sid} getrennt.")
    finally:
        with spiel_lock:
            del spielerdaten[sid]
        conn.close()

def server_starten():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", PORT))
    server.listen(MAX_SPIELER)
    print(f"Skyjo-Server läuft auf Port {PORT}")

    sid = 0
    while sid < MAX_SPIELER:
        conn, addr = server.accept()
        with spiel_lock:
            spielerdaten[sid] = {"conn": conn, "karten": []}
        threading.Thread(target=client_thread, args=(conn, sid), daemon=True).start()
        sid += 1

if __name__ == "__main__":
    server_starten()
