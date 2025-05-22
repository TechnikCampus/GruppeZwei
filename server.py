import socket
import threading
import pickle
import random
import time

# Globale Konfiguration
MAX_SPIELER = 8
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
    for spieler_id, info in spielerdaten.items():
        if exclude is not None and spieler_id == exclude:
            continue
        try:
            info["conn"].sendall(pickle.dumps(data))
        except (ConnectionResetError, EOFError, pickle.PickleError) as e:
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
        "typ": "start",
        "spieler_id": spieler_id,
        "karten": karten
    }
    conn.sendall(pickle.dumps(startdaten))

    try:
        while True:
            daten = pickle.loads(conn.recv(2048))
            if daten["typ"] == "bereit":
                with spiel_lock:
                    spielerdaten[spieler_id]["bereit"] = True
                print(f"Spieler {spieler_id} ist bereit.")
            elif daten["typ"] == "aktion":
                print(f"Aktionsdaten von Spieler {spieler_id}: {daten}")
                broadcast(
                    {
                        "typ": "aktion",
                        "spieler": spieler_id,
                        "inhalt": daten
                    },
                    exclude=spieler_id
                )
            elif daten["typ"] == "nachricht":
                broadcast({
                    "typ": "nachricht",
                    "von": spieler_id,
                    "text": daten["text"]
                })
    except (ConnectionResetError, EOFError, pickle.UnpicklingError) as e:
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
        "typ": "startinfo",
        "info": "Spiel beginnt jetzt!"
    })

if __name__ == "__main__":
    server_starten()
