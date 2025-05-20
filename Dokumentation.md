Dokumentation.txt

Anfangs gabe es eine oberflächliche Besprechung der Dinge & Einfälle.

Für das Skyio Projekt wurden verschiedene Ideen beigefügt: 

- Spielregeln und Punktesystem (geschicktes Flippen, Tauschen oder Ablegen von Karten möglichst viele Punkte zu erzielen)

- Steuerung (Spieler können Karten umdrehen, tauschen oder abgeben)

- Punktsysteme: Entwicklung des System für die Punktevergabe 

- Serverstruktur und Multiplayer 

- Serverkommunikation (über zentralen Server)

Zukünftig ist geplant, die Steuerung durch eine grafische Benutzeroberfläche (GUI) zu erweitern. 




Verwaltung der Spielzustände

Synchronisation der Eingaben aller Clients

Weiterleitung relevanter Spielinformationen

Verantwortlich für die Entwicklung des Servers:

Tom

Nice
Die beiden verwenden als technische Grundlage ein selbst entwickeltes Arcade-Spiel.

Unterstützende Entwickler:

Linus

Erhun

Musikplayer
Parallel zur Spielmechanik wird ein Musikplayer integriert, der Hintergrundmusik und Soundeffekte abspielt. Die Kommunikation zwischen Server und Player erfolgt je nach Architektur getrennt oder eingebettet.

4. Designkonzept
Das Spiel soll visuell ansprechend gestaltet werden. Der grafische Teil gliedert sich in folgende Komponenten:

Kartendesigns: Individuelle Vorder- und Rückseiten

Spielerdesigns: Avatare oder Spielfiguren

Welt und Tischdesign: Hintergrundbilder, Tischflächen, Umgebung

Ziel ist ein stimmiges Gesamtdesign, das sich am gewählten Spielstil orientiert (z. B. retro, modern, fantasievoll).

5. Startmenü, Highscore & Datenverarbeitung
Startmenü
Ein übersichtliches Startmenü ermöglicht dem Nutzer:

Spielstart

Anzeige der Highscores

Zugriff auf Einstellungen oder Spielregeln

Highscore-System
Die Punkte aller abgeschlossenen Spiele werden in einem zentralen Highscore-System gespeichert und angezeigt. Dieses System ermöglicht Vergleiche zwischen den Spielern und fördert den Wettbewerb.

Datenerarbeitung
Alle spielrelevanten Daten (Benutzereingaben, Spielverlauf, Punktevergabe) werden strukturiert verarbeitet und bei Bedarf gespeichert.

6. Client-Funktionalität
Der Client übernimmt in erster Linie die Erfassung und Weitergabe von Eingaben. Die Spiellogik bleibt größtenteils auf dem Server.
Beispielhafte Abläufe:

Aktion flippen → Eingabe wird vom Client an den Server gesendet → Server entscheidet über die Spielfolge → Rückmeldung an alle Clients.

Jeder Spieler sieht auf seinem Client denselben synchronisierten Zustand.

Zukünftig wird der Client um grafische Elemente erweitert, z. B. für Maussteuerung und Drag-and-Drop-Funktionen.

7. Projektorganisation und Zusammenarbeit
Die Aufgabenverteilung im Team erfolgt klar definiert. Zusätzlich zur Programmierung umfasst die Organisation folgende Bereiche:

Verwaltung: Planung und Koordination der Arbeitsschritte

Code-Zusammenführung: Einbindung aller Module in eine lauffähige Version (z. B. via Git)

Dokumentation: Begleitende Ausarbeitung technischer und gestalterischer Entscheidungen

Die Kommunikation im Team erfolgt regelmäßig zur Abstimmung des Entwicklungsfortschritts.

8. Theoretische Planungsphase (15. Mai)
Am 15. Mai wurde die Planungsphase durchgeführt. Inhalte der Besprechung:

Rollenverteilung im Team

Erste technische und gestalterische Konzepte

Diskussion der Umsetzbarkeit und Tools

Definition des Projektziels

Diese Sitzung legte den Grundstein für die darauf folgende Entwicklung des Grundgerüsts.

9. Technisches Grundgerüst
Ein erstes funktionsfähiges Grundgerüst wurde erstellt, um die Hauptfunktionen zu testen:

Aufbau der Server-Client-Kommunikation

Verarbeitung erster Eingaben (Flippen, Tauschen)

Platzhalter für Grafiken, Musik und Punktelogik

Dieses Grundgerüst bildet die technische Basis für alle weiteren Module.

