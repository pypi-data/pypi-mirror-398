import smartpy as sp
from smartpy.templates.chess import main, play

if "main" in __name__:
    player1 = sp.test_account("player1")
    player2 = sp.test_account("player2")

    @sp.add_test()
    def test():
        sc = sp.test_scenario("Chess - Checkmate")
        sc.h1("Checkmate")

        sc.h2("Scholar's mate")
        c1 = main.Chess(player1.address, player2.address)
        sc += c1

        c1.play(play(f=sp.record(i=1, j=4), t=sp.record(i=3, j=4)), _sender=player1)
        c1.play(play(f=sp.record(i=6, j=4), t=sp.record(i=4, j=4)), _sender=player2)
        c1.play(play(f=sp.record(i=0, j=5), t=sp.record(i=3, j=2)), _sender=player1)
        c1.play(play(f=sp.record(i=7, j=1), t=sp.record(i=5, j=2)), _sender=player2)
        c1.play(play(f=sp.record(i=0, j=3), t=sp.record(i=4, j=7)), _sender=player1)
        c1.claim_checkmate(_valid=False)
        c1.play(play(f=sp.record(i=6, j=0), t=sp.record(i=4, j=0)), _sender=player2)
        c1.claim_checkmate(_valid=False)
        c1.play(play(f=sp.record(i=4, j=7), t=sp.record(i=6, j=5)), _sender=player1)
        c1.claim_checkmate()

        sc.h2("King captures the attacking piece")
        c2 = main.Chess(player1.address, player2.address)
        sc += c2

        c2.play(play(f=sp.record(i=1, j=4), t=sp.record(i=3, j=4)), _sender=player1)
        c2.play(play(f=sp.record(i=6, j=4), t=sp.record(i=4, j=4)), _sender=player2)
        c2.play(play(f=sp.record(i=0, j=3), t=sp.record(i=2, j=5)), _sender=player1)
        c2.play(play(f=sp.record(i=7, j=1), t=sp.record(i=5, j=2)), _sender=player2)
        c2.play(play(f=sp.record(i=2, j=5), t=sp.record(i=6, j=5)), _sender=player1)
        c2.claim_checkmate(_valid=False)

        sc.h2("Suffocating King")
        c3 = main.Chess(player1.address, player2.address)
        sc += c3

        c3.play(play(f=sp.record(i=0, j=1), t=sp.record(i=2, j=2)), _sender=player1)
        c3.play(play(f=sp.record(i=6, j=4), t=sp.record(i=4, j=4)), _sender=player2)
        c3.play(play(f=sp.record(i=2, j=2), t=sp.record(i=4, j=3)), _sender=player1)
        c3.play(play(f=sp.record(i=7, j=6), t=sp.record(i=6, j=4)), _sender=player2)
        c3.play(play(f=sp.record(i=1, j=4), t=sp.record(i=3, j=4)), _sender=player1)
        c3.play(play(f=sp.record(i=6, j=6), t=sp.record(i=5, j=6)), _sender=player2)
        c3.play(play(f=sp.record(i=4, j=3), t=sp.record(i=5, j=5)), _sender=player1)
        sc.show(c3.build_fen())
        c3.claim_checkmate()

        sc.h2("Obstructing column")
        c4 = main.Chess(player1.address, player2.address)
        sc += c4

        c4.play(play(f=sp.record(i=0, j=1), t=sp.record(i=2, j=2)), _sender=player1)
        c4.play(play(f=sp.record(i=6, j=4), t=sp.record(i=4, j=4)), _sender=player2)
        c4.play(play(f=sp.record(i=1, j=4), t=sp.record(i=3, j=4)), _sender=player1)
        c4.play(play(f=sp.record(i=6, j=0), t=sp.record(i=4, j=0)), _sender=player2)
        c4.play(play(f=sp.record(i=0, j=3), t=sp.record(i=4, j=7)), _sender=player1)
        c4.play(play(f=sp.record(i=4, j=0), t=sp.record(i=3, j=0)), _sender=player2)
        c4.play(play(f=sp.record(i=4, j=7), t=sp.record(i=4, j=4)), _sender=player1)
        c4.claim_checkmate(_valid=False)

        sc.h2("Obstructing diagonal")
        c5 = main.Chess(player1.address, player2.address)
        sc += c5

        c5.play(play(f=sp.record(i=1, j=4), t=sp.record(i=3, j=4)), _sender=player1)
        c5.play(play(f=sp.record(i=6, j=5), t=sp.record(i=4, j=5)), _sender=player2)
        c5.play(play(f=sp.record(i=0, j=3), t=sp.record(i=4, j=7)), _sender=player1)
        c5.claim_checkmate(_valid=False)
        c5.play(play(f=sp.record(i=6, j=6), t=sp.record(i=5, j=6)), _sender=player2)
        c5.play(play(f=sp.record(i=1, j=7), t=sp.record(i=2, j=7)), _sender=player1)
        c5.play(play(f=sp.record(i=6, j=7), t=sp.record(i=5, j=7)), _sender=player2)
        c5.play(play(f=sp.record(i=4, j=7), t=sp.record(i=5, j=6)), _sender=player1)
        c5.claim_checkmate()
        sc.verify_equal(c5.data.status, sp.variant.finished("player_1_won"))
