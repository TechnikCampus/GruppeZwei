import socket
import pickle
import threading

# Dynamische Ermittlung der Server-IP über den Hostnamen
hostname = socket.gethostname()
SERVER_IP =  #Hier Server IP manuell eintragen !!!
PORT = 65433


def empfange_daten(client_socket):
    """
    Verarbeitung von Nachrichten, die vom Server empfangen werden.
    Läuft in einem separaten Thread.
    """
    try:
        while True:
            daten = pickle.loads(client_socket.recv(2048))

            if daten["typ"] == "start":
                print(f"Deine Karten: {daten['karten']}")
                client_socket.sendall(
                    pickle.dumps({"typ": "bereit"})
                )

            elif daten["typ"] == "aktion":
                print(
                    f"Aktion von Spieler {daten['spieler']}: {daten['inhalt']}"
                )

            elif daten["typ"] == "nachricht":
                print(
                    f"Nachricht von Spieler {daten['von']}: {daten['text']}"
                )

            elif daten["typ"] == "startinfo":
                print(daten["info"])

            else:
                print(f"Unbekannter Nachrichtentyp: {daten}")
    except Exception as e:
        print(f"Verbindungsfehler: {e}")
    finally:
        client_socket.close()


def sende_nachrichten(client_socket):
    """
    Verarbeitung der Benutzereingaben.
    Sendet Nachrichten an den Server.
    """
    try:
        while True:
            nachricht = input("Nachricht eingeben (oder 'exit'): ")
            if nachricht.strip().lower() == "exit":
                break
            if nachricht.strip():
                client_socket.sendall(
                    pickle.dumps({
                        "typ": "nachricht",
                        "text": nachricht.strip()
                    })
                )
    except Exception as e:
        print(f"Fehler beim Senden: {e}")
    finally:
        client_socket.close()


def main():
    """
    Hauptfunktion:
    - Verbindet zum Server
    - Startet Empfangs- und Sendethreads
    """
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect((SERVER_IP, PORT))
        print(f"Verbunden mit dem Server ({SERVER_IP}:{PORT})")

        # Thread starten, um eingehende Daten zu empfangen
        empfangs_thread = threading.Thread(
            target=empfange_daten,
            args=(client,),
            daemon=True
        )
        empfangs_thread.start()

        # Eingaben des Nutzers senden
        sende_nachrichten(client)

    except ConnectionRefusedError:
        print(f"Verbindung zum Server nicht möglich ({SERVER_IP}:{PORT})")
    except Exception as e:
        print(f"Unerwarteter Fehler: {e}")
    finally:
        client.close()
        print("Verbindung geschlossen.")


if __name__ == "__main__":
    main()
