import socket
import threading
import json
import random
import time

# Globale Konfiguration
MAX_SPIELER = 4
PORT = 65433
KARTEN_PRO_SPIELER = 12

# Karten von Skyjo (vereinfachtes Deck für das Beispiel)
KARTEN_DECK = [-2] * 5 + list(range(0, 13)) * 10
random.shuffle(KARTEN_DECK)

# Spielzustände
verbindungen = []
spielerdaten = {}
spiel_lock = threading.Lock()
spielgestartet = False

def karten_ziehen(anzahl):
    return [KARTEN_DECK.pop() for _ in range(anzahl) if KARTEN_DECK]

def broadcast(data, exclude=None):
    message = json.dumps(data).encode("utf-8") + b"\n"
    for spieler_id, info in spielerdaten.items():
        if exclude is not None and spieler_id == exclude:
            continue
        try:
            info["conn"].sendall(message)
        except (ConnectionResetError, BrokenPipeError) as e:
            print(f"Fehler beim Senden: {e}")

def warte_auf_bereitschaft():
    """Blockiert bis alle Spieler sich als bereit gemeldet haben."""
    while True:
        with spiel_lock:
            alle_bereit = all(
                spieler.get("bereit", False)
                for spieler in spielerdaten.values()
            )
        if alle_bereit:
            print("Alle Spieler sind bereit. Spiel startet!")
            return
        time.sleep(1)

def client_thread(conn, spieler_id):
    global spielgestartet
    print(f"Thread für Spieler {spieler_id} gestartet.")

    # Karten zuteilen
    karten = karten_ziehen(KARTEN_PRO_SPIELER)
    with spiel_lock:
        spielerdaten[spieler_id]["karten"] = karten

    # Anfangsdaten senden
    startdaten = {
        "type": "start",
        "player_id": spieler_id,
        "hand": karten
    }
    conn.sendall(json.dumps(startdaten).encode("utf-8") + b"\n")

    buffer = b""
    try:
        while True:
            chunk = conn.recv(4096)
            if not chunk:
                break
            buffer += chunk
            while b"\n" in buffer:
                raw_msg, buffer = buffer.split(b"\n", 1)
                try:
                    daten = json.loads(raw_msg.decode("utf-8"))
                    if daten["type"] == "ready":
                        with spiel_lock:
                            spielerdaten[spieler_id]["bereit"] = True
                        print(f"Spieler {spieler_id} ist bereit.")
                    elif daten["type"] == "draw_card":
                        karte = karten_ziehen(1)[0] if KARTEN_DECK else None
                        with spiel_lock:
                            spielerdaten[spieler_id]["karten"].append(karte)
                        conn.sendall(json.dumps({
                            "type": "card_drawn",
                            "card": karte
                        }).encode("utf-8") + b"\n")
                    elif daten["type"] == "chat":
                        broadcast({
                            "type": "chat",
                            "sender": daten.get("sender", "?"),
                            "text": daten.get("text", "")
                        })
                    elif daten["type"] == "reveal_card":
                        broadcast({
                            "type": "reveal_result",
                            "data": daten.get("data", {}),
                            "player": spieler_id
                        })
                    elif daten["type"] == "discard_card":
                        broadcast({
                            "type": "discarded",
                            "data": daten.get("data", {}),
                            "player": spieler_id
                        })
                    elif daten["type"] == "swap_card":
                        broadcast({
                            "type": "swapped",
                            "data": daten.get("data", {}),
                            "player": spieler_id
                        })
                    elif daten["type"] == "pass_card":
                        broadcast({
                            "type": "passed",
                            "player": spieler_id
                        })
                except json.JSONDecodeError:
                    print("Fehler beim Dekodieren der Nachricht")
    except (ConnectionResetError, BrokenPipeError) as e:
        print(f"Spieler {spieler_id} getrennt: {e}")
    finally:
        conn.close()
        with spiel_lock:
            if spieler_id in spielerdaten:
                del spielerdaten[spieler_id]

def server_starten():
    global spielgestartet
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", PORT))
    server.listen(MAX_SPIELER)
    print(f"Skyjo-Server gestartet auf Port {PORT}.")

    spieler_id = 0
    while spieler_id < MAX_SPIELER:
        conn, addr = server.accept()
        print(f"Spieler {spieler_id} verbunden: {addr}")
        with spiel_lock:
            spielerdaten[spieler_id] = {
                "conn": conn,
                "karten": [],
                "bereit": False
            }
        verbindungen.append(conn)
        thread = threading.Thread(
            target=client_thread,
            args=(conn, spieler_id)
        )
        thread.start()
        spieler_id += 1

    warte_auf_bereitschaft()
    spielgestartet = True
    broadcast({
        "type": "game_state",
        "info": "Spiel beginnt jetzt!"
    })

if __name__ == "__main__":
    server_starten()
