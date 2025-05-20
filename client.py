import socket
import pickle

# Dynamische Ermittlung der Server-IP basierend auf dem Hostnamen
hostname = socket.gethostname()
SERVER_IP = socket.gethostbyname(hostname)  # Ermittelt die IP-Adresse des Servers
PORT = 65433

def main():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((SERVER_IP, PORT))
    print(f"Verbunden mit dem Server ({SERVER_IP}).")

    try:
        while True:
            daten = pickle.loads(client.recv(2048))
            print(f"Empfangen: {daten}")

            if daten["typ"] == "start":
                print(f"Deine Karten: {daten['karten']}")
                client.sendall(pickle.dumps({"typ": "bereit"}))

            elif daten["typ"] == "aktion":
                print(f"Aktionsdaten: {daten}")

            elif daten["typ"] == "nachricht":
                print(f"Nachricht von Spieler {daten['von']}: {daten['text']}")

            # Beispiel: Nachricht an andere Spieler senden
            nachricht = input("Nachricht eingeben (oder 'exit' zum Beenden): ")
            if nachricht.lower() == "exit":
                break
            client.sendall(pickle.dumps({"typ": "nachricht", "text": nachricht}))
    except Exception as e:
        print(f"Fehler: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    main()