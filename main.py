import tkinter as tk
from tkinter import simpledialog, messagebox
import threading
import socket
from PIL import Image, ImageTk

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
        print(IP)
    except Exception:
        IP = "127.0.0.1"
    finally:
        s.close()
    return IP


def start_host():
    try:
        spieler = simpledialog.askinteger("Einstellungen", "Wie viele Spieler?")
        runden = simpledialog.askinteger("Einstellungen", "Wie viele Runden?")
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
    root.geometry("700x400")
    for col in range(6):
        root.grid_columnconfigure(col, minsize=80)
    root.resizable(False, False)

    # Lobby-Hintergrund
    try:
        lobby_img = ImageTk.PhotoImage(Image.open("Lobby.png"))
        bg_label = tk.Label(root, image=lobby_img)
        bg_label.place(relwidth=1, relheight=1)
        bg_label.lower()  # ganz nach unten
    except Exception as e:
        print(f"[WARN] Lobby.png konnte nicht geladen werden: {e}")

    # Auswahl-Frame
    frame = tk.Frame(root, bg="white")
    frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

    tk.Label(frame, text="Wähle Modus", font=("Arial", 14), bg="white").pack(pady=10)
    tk.Button(frame, text="Host starten", width=20, command=start_host).pack(pady=5)
    tk.Button(frame, text="Client verbinden", width=20, command=start_client).pack(pady=5)

    root.mainloop()
