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
import settings as s

anzahlSpieler = 4   # Anzahl der Spieler, soll vom Host empfangen werden
anzahlSpiel = 4     # Anzahl der zu spielenden Spiel, vom Host
firstTurn = 1
lastTurn = anzahlSpieler - 1
end_player_index = None

SkyjoSpiel = SkyjoGame()

for i in range(anzahlSpieler):
    Spieler = Player(i, )
    SkyjoSpiel.add_player(Spieler)

for u in range(anzahlSpiel):

    lastTurn = anzahlSpieler - 1
    end_player_index = None

    for spieler in SkyjoSpiel.players:
        SkyjoSpiel.player_ready(spieler)

    for spieler in SkyjoSpiel.players:
        pass  # spielerdeck jedem client mit teilen

    if SkyjoSpiel.all_ready():
        while (firstTurn <= 2 * anzahlSpieler):
            SkyjoSpiel.wait_for_communication()     # muss noch programmiert werdden/ wartet bis alle daten da sind
            reihe = 0       # informationen vom client
            spalte = 0      # informationen vom client
            abfrage1 = 1    # informationen vom client
            abfrage2 = 2    # informationen vom client

            aktuellerSpieler = SkyjoSpiel.get_current_player()
            aktuellerSpieler.reveal_card(reihe, spalte)
            aktuellerSpieler.calculate_score()
            SkyjoSpiel.next_turn()
            firstTurn += 1
        else:
            exit()

    SkyjoSpiel.sort_players()

    while (SkyjoSpiel.all_ready()):

        SkyjoSpiel.wait_for_communication()     # muss noch programmiert werdden/ wartet bis alle daten da sind
        reihe = 0       # informationen vom client
        spalte = 0      # informationen vom client
        abfrage1 = 1    # informationen vom client
        abfrage2 = 2    # informationen vom client

        aktuellerSpieler = SkyjoSpiel.get_current_player()

        match (abfrage1):
            case (s.KARTEVOMSTAPELNEHMEN):
                karte = aktuellerSpieler.get_card(reihe, spalte)         # r und c müssen vom client übergeben werden
                aktuellerSpieler.set_card(reihe, spalte, SkyjoSpiel.discard_pile.pop())
                aktuellerSpieler.reveal_card(reihe, spalte)
                SkyjoSpiel.discard_pile.append(karte)
            case (s.KARTEVOMSTAPELAUFDECKEN):
                SkyjoSpiel.player_draw_new_card(aktuellerSpieler)
                match (abfrage2):
                    case(s.KARTEVOMSTAPELNEHMEN):
                        karte = aktuellerSpieler.get_card(reihe, spalte)         # r und c müssen vom client übergeben werden
                        aktuellerSpieler.set_card(reihe, spalte, SkyjoSpiel.discard_pile.pop())
                        aktuellerSpieler.reveal_card(reihe, spalte)
                        SkyjoSpiel.discard_pile.append(karte)
                    case(s.EIGENEKARTEAUFDECKEN):
                        aktuellerSpieler.reveal_card(reihe, spalte)

        SkyjoSpiel.threeSome()

        if (SkyjoSpiel.check_for_end(aktuellerSpieler)) and (end_player_index is None):
            end_player_index = SkyjoSpiel.current_turn
        elif (end_player_index is not None):
            lastTurn -= 1
            if lastTurn == 0:
                break

        SkyjoSpiel.next_turn()

    SkyjoSpiel.reset_game()
