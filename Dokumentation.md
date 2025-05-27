Dokumentation.txt

Anfangs gabe es eine oberflächliche Besprechung der Dinge & Einfälle.

Für das Skyio Projekt wurden verschiedene Ideen beigefügt: 

- Spielregeln und Punktesystem (geschicktes Flippen, Tauschen oder Ablegen von Karten möglichst viele Punkte zu erzielen)

- Steuerung (Spieler können Karten umdrehen, tauschen oder abgeben)

- Punktsysteme: Entwicklung des System für die Punktevergabe 

- Serverstruktur und Multiplayer 

- Serverkommunikation (über zentralen Server)



Zukünftig ist geplant, die Steuerung durch eine grafische Benutzeroberfläche (GUI) zu erweitern. 



Client/ Erfassung und Weitergabe von Eingaben/ Input: Avinash
Zum Beispiel: Aktion flippen → Eingabe wird vom Client an den Server gesendet → Server entscheidet über die Spielfolge → Rückmeldung an alle Clients.
Elemente synchronisieren

Verantwortlich für die Entwicklung des Servers: Linus

Struktur & später Serverkommunikation: Nico & Tom



Designkonzept

- Kartendesigns: Individuelle Vorder- und Rückseiten

- Welt und Tischdesign: Hintergrundbilder, Tischflächen, Umgebung



Projektorganisation und Zusammenarbeit
bisher erfolgte dies so:

- Verwaltung: Planung und Koordination der Arbeitsschritte

- regelmäßige Treffen und aktivie Kommunikaion zur Abstimmung des Entwicklungsfortschritts




Theoretische Planungsphase (15. Mai)
Am 15. Mai wurde die Planungsphase durchgeführt

Inhalte der Besprechung:

- Rollenverteilung im Team

- Erste technische und gestalterische Konzepte

- Diskussion der Umsetzbarkeit und Tools

- Projektziel erfassen

(Schriftführer bis jetzt Avinash)

Protokoll – Stand 22. Mai

1. Technische Probleme und Lösungen

Es gab anfangs Probleme mit der Verbindung zum Server über den Arbeitslaptop, da dessen Firewall die Verbindung blockierte.

Zur Umgehung des Problems wurde ein Ersatzlaptop organisiert, mit dem die Serververbindung erfolgreich hergestellt werden konnte.

2. Fehler im Client-Skript

Im Client-Skript trat ein Problem auf, weil die automatische IP-Adresskonfiguration nicht zuverlässig funktionierte. Diese Methode funktionierte lediglich im lokalen Host-Betrieb.

Als Lösung wurde auf eine manuelle Eingabe der IP-Adresse umgestellt.

Eine mögliche zukünftige Erweiterung ist ein Eingabefeld (Input), über das Nutzer beim Start des Clients angeben können, mit welcher IP-Adresse sie sich verbinden möchten.

3. Kommunikation mit dem Server

Die Konfiguration für das Senden von Nachrichten an den Server wurde erfolgreich eingerichtet.

Wichtige Variablen wie z. B. „bereit“ oder „aktion“ wurden definiert, um den Kommunikationsfluss zwischen Client und Server zu steuern.

Es wurde ein Dictionary implementiert, das Rückmeldungen wie „OK“ oder die Bereitschaft des Spielers verarbeitet.

4. Spiellogik

Die Funktion zur Zuteilung von Spielerkarten wurde implementiert.

In der weiteren Spiellogik wird umgesetzt, dass eine Reihe gelöscht wird, sobald ein Spieler eine Karte mit der gleichen Zahl legt (dies wird von Linus weiterentwickelt).

Zudem soll unterschieden werden, ob ein Spieler hostet oder einem bestehenden Spiel beitritt. Wenn gehostet wird, startet der Client automatisch einen Server.

In beiden Fällen (Host oder Beitritt) wird beim Start ein Pop-up-Fenster erscheinen, in dem die gewünschte IP-Adresse eingegeben werden kann.

5. Geplante Features

Entwicklung einer grafischen Darstellung der Spielkarten im Client:

Zunächst soll die eigene Kartenhand angezeigt werden.

Später auch die Kartensätze der anderen Spieler (z. B. als verdeckte Karten oder in vereinfachter Darstellung).


Erstellung eines Hauptmenüs:

Auswahlmöglichkeit: „Host starten“ oder „Spiel beitreten“.

Bei Auswahl von „Host“ wird der Server initialisiert.

Bei Auswahl von „Beitreten“ erfolgt die IP-Eingabe und die Verbindung zum bestehenden Server.
