##############################################################################
# Projekt:  Skyjo
# Datei:    skyjo.py
# Autor:    Linus Wohlgemuth (Grinzold86), Nico Leder (xNox33), Avinash Suthakaran (Avinash21-creator), Tom Holst (tomholst)
# Datum:    19.5.2025
# Version:  1.0
##############################################################################
# Beschreibung:
##############################################################################
from class_player import Player
from SkyjoGame import SkyjoGame
# import pygame

anzahlSpieler = 4  # Anzahl der Spieler, soll vom Host empfangen werden

SkyjoSpiel = SkyjoGame()

for i in range(anzahlSpieler):
    Spieler = Player()
    SkyjoSpiel.add_player(Spieler)

for spieler in SkyjoSpiel.players:
    SkyjoSpiel.player_ready(spieler)

while SkyjoSpiel.all_ready():
    aktuellerSpieler = SkyjoSpiel.get_current_player()
    aktuellerSpieler.reveal_card(0, 1)
    aktuellerSpieler.reveal_card(0, 3)


