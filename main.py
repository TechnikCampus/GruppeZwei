# ==== Importierte Module ====
import tkinter as tk
from tkinter import simpledialog, messagebox  # Für Eingabe- und Hinweisfenster
import threading  # Für parallelen Serverstart
import socket     # Für IP-Ermittlung
from PIL import Image, ImageTk  # Für Hintergrundbildanzeige

# Eigene Module
from Server_Client import server_starten, PORT  # Serverstartfunktion & Portkonstante
from client_gui import GameGUI  # Client-GUI-Klasse

# ==== Globale Spielkonfiguration ====
config = {
    "anzahl_spieler": 2,  # Standardanzahl Spieler
    "anzahl_runden": 1    # Standardanzahl Runden
}


# ==== Lokale IP-Adresse des Hosts ermitteln ====
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))  # Dummy-Adresse zum Ermitteln der lokalen IP
        IP = s.getsockname()[0]
        print(IP)  # IP ausgeben (Debug-Zwecke)
    except Exception:
        IP = "127.0.0.1"  # Fallback: localhost
    finally:
        s.close()
    return IP


# ==== Spiel als Host starten ====
def start_host():
    try:
        # Spieleranzahl und Rundenzahl abfragen
        spieler = simpledialog.askinteger("Einstellungen", "Wie viele Spieler?")
        runden = simpledialog.askinteger("Einstellungen", "Wie viele Runden?")
        if not spieler or not runden:
            raise ValueError("Ungültige Eingabe")

        # Konfiguration setzen
        config["anzahl_spieler"] = spieler
        config["anzahl_runden"] = runden

    except:
        # Fehlermeldung bei ungültiger Eingabe
        messagebox.showerror("Fehler", "Abbruch wegen ungültiger Eingabe.")
        return

    ip = get_local_ip()  # Eigene IP-Adresse holen

    # Server im Hintergrund-Thread starten
    threading.Thread(target=server_starten, args=(config,), daemon=True).start()

    # Hinweisfenster: Server wurde gestartet
    messagebox.showinfo("Host gestartet", f"Server läuft auf IP: {ip}")

    # Startfenster schließen
    root.destroy()

    # Neues Fenster mit Spiel-GUI (Client für Host)
    gui_root = tk.Tk()
    app = GameGUI(gui_root, "localhost", PORT)
    gui_root.mainloop()


# ==== Als Client einem Spiel beitreten ====
def start_client():
    ip = simpledialog.askstring("Client", "Gib die IP-Adresse des Hosts ein:")
    if ip:
        root.destroy()  # Startfenster schließen
        gui_root = tk.Tk()
        app = GameGUI(gui_root, ip, PORT)  # Mit Host verbinden
        gui_root.mainloop()


# ==== Rangliste anzeigen ====
def zeige_rangliste(spieler_punkte):
    """
    Zeigt die Rangliste der Spieler nach Spielende an.
    
    Args:
        spieler_punkte: Dictionary mit Spielernamen und finalen Punkten
    """
    print(f"[DEBUG] ====== RANKING CREATION START ======")
    print(f"[DEBUG] Received scores: {spieler_punkte}")
    
    # Bubble Sort für die Sortierung nach Punkten
    def bubble_sort_scores(scores):
        """Sort players by score in ascending order"""
        items = list(scores.items())
        n = len(items)
        print(f"[DEBUG] Starting sort with scores: {items}")
        
        for i in range(n):
            for j in range(0, n-i-1):
                # Convert scores to integers with error handling
                try:
                    score1 = int(items[j][1])
                    score2 = int(items[j+1][1])
                except (TypeError, ValueError) as e:
                    print(f"[DEBUG] Score conversion error: {e}")
                    continue
                    
                print(f"[DEBUG] Comparing {items[j][0]} ({score1}) with {items[j+1][0]} ({score2})")
                if score1 > score2:
                    items[j], items[j+1] = items[j+1], items[j]
                    print(f"[DEBUG] Swapped positions")
        
        print(f"[DEBUG] Final sorted order: {items}")
        return items
    
    sortierte_spieler = bubble_sort_scores(spieler_punkte)
    print(f"[DEBUG] Sorted players: {sortierte_spieler}")
    
    # GUI Setup
    rangliste_fenster = tk.Toplevel()
    rangliste_fenster.title("Rangliste")
    rangliste_fenster.geometry("700x400")
    rangliste_fenster.resizable(False, False)
    rangliste_fenster.focus_force()  # Force focus on ranking window
    rangliste_fenster.grab_set()     # Make window modal

    # Timer Label hinzufügen
    timer_label = tk.Label(rangliste_fenster, text="Fenster schließt in 30 Sekunden...", 
                          font=("Arial", 10), bg="white")
    timer_label.place(relx=0.5, rely=0.9, anchor=tk.CENTER)

    # Countdown Funktion
    def countdown(remaining):
        if remaining > 0:
            timer_label.config(text=f"Fenster schließt in {remaining} Sekunden...")
            rangliste_fenster.after(1000, countdown, remaining - 1)
        else:
            print("[DEBUG] Closing ranking window after 30 seconds")
            rangliste_fenster.quit()
            rangliste_fenster.destroy()

    # Start 30 second countdown
    rangliste_fenster.after(1000, countdown, 30)
    
    try:
        # Rangliste-Hintergrundbild laden und skalieren
        img = Image.open("assets/rangliste.png")
        img = img.resize((700, 400), Image.LANCZOS)  # Resize to window size
        rangliste_img = ImageTk.PhotoImage(img)
        bg_label = tk.Label(rangliste_fenster, image=rangliste_img)
        bg_label.image = rangliste_img  # Keep reference
        bg_label.place(relwidth=1, relheight=1)
        print("[DEBUG] Ranking background image loaded and scaled")
    except Exception as e:
        print(f"[WARN] Could not load rangliste.png: {e}")

    # Frame für die Rangliste
    rang_frame = tk.Frame(rangliste_fenster, bg='white', bd=2, relief='solid')
    rang_frame.place(relx=0.5, rely=0.4, anchor=tk.CENTER)
    
    # Überschrift
    tk.Label(rang_frame, 
            text="🏆 Rangliste 🏆",
            font=("Arial", 16, "bold"),
            bg='white').pack(pady=10)
    
    # Rangliste erstellen mit sortierten Spielern
    for position, (spieler, punkte) in enumerate(sortierte_spieler, 1):
        name = spieler.split(" als ")[1].rstrip('.')
        platz_text = f"{position}. Platz: {name}"  # Only show name
        
        print(f"[DEBUG] Adding player to ranking: {name} with {punkte} points")
        
        label_style = {"font": ("Arial", 12),
                      "bg": 'white',
                      "padx": 10,
                      "pady": 5}
        
        if position == 1:
            label_style["fg"] = "gold"
            platz_text = "🥇 " + platz_text
        elif position == 2:
            label_style["fg"] = "silver"
            platz_text = "🥈 " + platz_text
        elif position == 3:
            label_style["fg"] = "#CD7F32"
            platz_text = "🥉 " + platz_text
            
        tk.Label(rang_frame, text=platz_text, **label_style).pack()
    
    # Schließen-Button
    tk.Button(rang_frame,
              text="Schließen",
              command=rangliste_fenster.destroy).pack(pady=10)

    # Keep window open
    rangliste_fenster.mainloop()


# ==== Hauptfenster: Auswahl Host oder Client ====
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Skyjo starten")
    root.geometry("700x400")  # Fenstergröße

    # Spalten konfigurieren (für Zentrierung)
    for col in range(6):
        root.grid_columnconfigure(col, minsize=80)

    root.resizable(False, False)  # Kein Resize zulassen

    # ==== Versuche Hintergrundbild zu laden ====
    try:
        lobby_img = ImageTk.PhotoImage(Image.open("assets/Lobby.png"))
        bg_label = tk.Label(root, image=lobby_img)
        bg_label.place(relwidth=1, relheight=1)  # Vollbildanzeige
        bg_label.lower()  # Bild ganz nach hinten
    except Exception as e:
        print(f"[WARN] Lobby.png konnte nicht geladen werden: {e}")

    # ==== Rahmen für Button-Auswahl ====
    frame = tk.Frame(root, bg="white")
    frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)  # Mitte des Fensters

    # Titel und Buttons
    tk.Label(frame, text="Wähle Modus", font=("Arial", 14), bg="white").pack(pady=10)
    tk.Button(frame, text="Host starten", width=20, command=start_host).pack(pady=5)
    tk.Button(frame, text="Client verbinden", width=20, command=start_client).pack(pady=5)

    # Hauptloop starten (Fensteranzeige)
    root.mainloop()
