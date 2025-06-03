##############################################################################
# Projekt:  Skyjo
# Datei:    skyjo.py
# Autor:    Linus Wohlgemuth (Grinzold86), Nico Leder (xNox33), Avinash Suthakaran (Avinash21-creator)
# Datum:    19.5.2025
# Version:  1.0
##############################################################################
# Beschreibung:
##############################################################################
import player as Player
import random
# import pygame

<<<<<<< Updated upstream
anzahlSpieler = 4   # Anzahl der Spieler / muss über den Host festgelegt werden
=======




anzahlSpieler = 4   # Anzahl der Spieler, soll vom Host empfangen werden
anzahlSpiel = 4     # Anzahl der zu spielenden Spiel, vom Host
firstTurn = 1
lastTurn = anzahlSpieler - 1
end_player_index = None
>>>>>>> Stashed changes

skyjo_karten = (
    *([-2] * 5),
    *([-1] * 10),
    *([0] * 15),
    *([1] * 10),
    *([2] * 10),
    *([3] * 10),
    *([4] * 10),
    *([5] * 10),
    *([6] * 10),
    *([7] * 10),
    *([8] * 10),
    *([9] * 10),
    *([10] * 10),
    *([11] * 10),
    *([12] * 10)
)

umgedrehteKarten = []
aufgedeckteKarten = []

spielerTupel = []
for j in range(1, anzahlSpieler):
    index = random.randint(0, len(skyjo_karten) - 1)
    for i in range(1, 12):
        umgedrehteKarten[i] = skyjo_karten[index]
        skyjo_karten.pop(index)   # Karten ziehen
    Spieler = Player(j, umgedrehteKarten)
    spielerTupel.append(Spieler)    # Spieler-Objekte erstellen und in einer Liste speichern mit seinen Karten
