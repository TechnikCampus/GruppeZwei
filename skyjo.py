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

anzahlSpieler = 4  # Anzahl der Spieler

SkyjoSpiel = SkyjoGame()
SkyjoSpiel.initialize_deck()  # Kartenstapel initialisieren
SkyjoSpiel.deal_initial_cards()  # Karten austeilen

umgedrehteKarten = []
aufgedeckteKarten = []
