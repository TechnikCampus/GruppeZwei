import tkinter as tk
from tkinter import simpledialog, messagebox
import threading
import socket

from Server_Client import server_starten, PORT
from client_gui import GameGUI

# Globale Konfiguration
config = {
    "anzahl_spieler": 2,
    "anzahl_runden": 1
}


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = "127.0.0.1"
    finally:
        s.close()
    return IP


def start_host():
    # Spieleranzahl und Rundenzahl abfragen
    try:
        spieler = simpledialog.askinteger("Einstellungen", "Wie viele Spieler?")
        runden = simpledialog.askinteger("Einstellungen", "Wie viele Spiele?")
        if not spieler or not runden:
            raise ValueError("Ungültige Eingabe")
        config["anzahl_spieler"] = spieler
        config["anzahl_runden"] = runden
    except:
        messagebox.showerror("Fehler", "Abbruch wegen ungültiger Eingabe.")
        return

    ip = get_local_ip()
    threading.Thread(target=server_starten, args=(config,), daemon=True).start()
    messagebox.showinfo("Host gestartet", f"Server läuft auf IP: {ip}")
    root.destroy()

    gui_root = tk.Tk()
    app = GameGUI(gui_root, "localhost", PORT)
    gui_root.mainloop()


def start_client():
    ip = simpledialog.askstring("Client", "Gib die IP-Adresse des Hosts ein:")
    if ip:
        root.destroy()
        gui_root = tk.Tk()
        app = GameGUI(gui_root, ip, PORT)
        gui_root.mainloop()


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Skyjo starten")
    tk.Label(root, text="Wähle Modus").pack(pady=10)
    tk.Button(root, text="Host starten", width=20, command=start_host).pack(pady=5)
    tk.Button(root, text="Client verbinden", width=20, command=start_client).pack(pady=5)
    root.mainloop()
