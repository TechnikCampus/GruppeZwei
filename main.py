import tkinter as tk
from tkinter import simpledialog, messagebox
import threading
import socket

from Server_Client import server_starten, PORT
from client_gui import GameGUI

# Globale Konfiguration
config = {                                                  # Voreinstellungen
    "anzahl_spieler": 2,
    "anzahl_runden": 1
}


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)    # UDP Socket erstellen
    try:
        s.connect(("10.255.255.255", 1))                    # Verbindungsaufbau mit nicht erreichbaren IP
        IP = s.getsockname()[0]                             # gibt IP des Servers wieder
    except Exception:
        IP = "127.0.0.1"                                    # falls keine ermittelt werden konnte wird 127.0.0.1 wiedergegeben
    finally:
        s.close()                                           # Socket wrird wieder geschlossen
    return IP


def start_host():
    try:
        spieler = simpledialog.askinteger("Einstellungen", "Wie viele Spieler?")        # Abfrage wie viele Spieler betreiten
        runden = simpledialog.askinteger("Einstellungen", "Wie viele Spiele?")          # Abfrage wie viele Spiele gespielt werden soll
        if not spieler or not runden:                                                   # Falscheingabe
            raise ValueError("Ungültige Eingabe")
        config["anzahl_spieler"] = spieler                                              # config Dictionary aktualisieren mit neuen Werten
        config["anzahl_runden"] = runden
    except:
        messagebox.showerror("Fehler", "Abbruch wegen ungültiger Eingabe.")             # Fehlermeldung bei Falscheingabe
        return

    ip = get_local_ip()                                                                 # Server IP
    threading.Thread(target=server_starten, args=(config,), daemon=True).start()        # startet neuen Thread, Server wird gestartet (daemon=true) bedeutet dass sich der Server automatisch schliesst
    messagebox.showinfo("Host gestartet", f"Server läuft auf IP: {ip}")                 # Zeigt die IP in serperatem Fenster
    root.destroy()                                                                      # Schliesst Auswahlfenster Host/Client

    gui_root = tk.Tk()                                                                  # erstellt neues Tkinker Hauptfenster
    app = GameGUI(gui_root, "localhost", PORT)
    gui_root.mainloop()                                                                 # startet die Hauptschleife des GUI Fensters


def start_client():
    ip = simpledialog.askstring("Client", "Gib die IP-Adresse des Hosts ein:")
    if ip:
        root.destroy()
        gui_root = tk.Tk()
        app = GameGUI(gui_root, ip, PORT)
        gui_root.mainloop()


if __name__ == "__main__":                                                              # startet nur wenn main.py gestartet wurde
    root = tk.Tk()                                                                      # erstellt Fenster des Auswahlmenus
    root.title("Skyjo starten")
    tk.Label(root, text="Wähle Modus").pack(pady=10)                                    # Text im Auswahlmenu
    tk.Button(root, text="Host starten", width=20, command=start_host).pack(pady=5)     # Button Host
    tk.Button(root, text="Client verbinden", width=20, command=start_client).pack(pady=5)   # Button Client
    root.mainloop()
