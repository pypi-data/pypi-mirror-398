import smartpy as sp
from smartpy.templates.chess import build_fen, main, play

if "main" in __name__:
    player1 = sp.test_account("player1")
    player2 = sp.test_account("player2")

    @sp.add_test()
    def test():
        sc = sp.test_scenario("Chess - 3 times repeat")
        c1 = main.Chess(player1.address, player2.address)

        sc.h1("3 times repeat")
        sc.h2("After move")
        sc += c1

        c1.play(play(f=sp.record(i=0, j=6), t=sp.record(i=2, j=5)), _sender=player1)
        c1.play(play(f=sp.record(i=7, j=1), t=sp.record(i=5, j=2)), _sender=player2)
        c1.play(play(f=sp.record(i=2, j=5), t=sp.record(i=0, j=6)), _sender=player1)
        c1.play(play(f=sp.record(i=5, j=2), t=sp.record(i=7, j=1)), _sender=player2)
        c1.play(play(f=sp.record(i=0, j=6), t=sp.record(i=2, j=5)), _sender=player1)
        c1.play(play(f=sp.record(i=7, j=1), t=sp.record(i=5, j=2)), _sender=player2)
        c1.play(play(f=sp.record(i=2, j=5), t=sp.record(i=0, j=6)), _sender=player1)
        c1.play(play(f=sp.record(i=5, j=2), t=sp.record(i=7, j=1)), _sender=player2)
        c1.play(play(f=sp.record(i=0, j=6), t=sp.record(i=2, j=5)), _sender=player1)
        c1.play(play(f=sp.record(i=7, j=1), t=sp.record(i=5, j=2)), _sender=player2)
        c1.play(play(f=sp.record(i=2, j=5), t=sp.record(i=0, j=6)), _sender=player1)
        c1.play(
            play(
                f=sp.record(i=5, j=2),
                t=sp.record(i=7, j=1),
                claim_repeat=sp.Some((0, 3)),
            ),
            _sender=player2,
            _valid=False,
            _exception=sp.pair("NotSameMove", sp.record(fullMove=3)),
        )
        c1.play(
            play(
                f=sp.record(i=5, j=2),
                t=sp.record(i=7, j=1),
                claim_repeat=sp.Some((0, 4)),
            ),
            _sender=player2,
        )
        sc.verify(c1.data.status == sp.variant.finished("draw"))

        sc.h2("Previous move")
        c2 = main.Chess(player1.address, player2.address)
        sc += c2

        c2.play(play(f=sp.record(i=0, j=6), t=sp.record(i=2, j=5)), _sender=player1)
        c2.play(play(f=sp.record(i=7, j=1), t=sp.record(i=5, j=2)), _sender=player2)
        c2.play(play(f=sp.record(i=2, j=5), t=sp.record(i=0, j=6)), _sender=player1)
        c2.play(play(f=sp.record(i=5, j=2), t=sp.record(i=7, j=1)), _sender=player2)
        c2.play(play(f=sp.record(i=0, j=6), t=sp.record(i=2, j=5)), _sender=player1)
        c2.play(play(f=sp.record(i=7, j=1), t=sp.record(i=5, j=2)), _sender=player2)
        c2.play(play(f=sp.record(i=2, j=5), t=sp.record(i=0, j=6)), _sender=player1)
        c2.play(play(f=sp.record(i=5, j=2), t=sp.record(i=7, j=1)), _sender=player2)
        c2.play(play(f=sp.record(i=0, j=6), t=sp.record(i=2, j=5)), _sender=player1)
        c2.play(play(f=sp.record(i=7, j=1), t=sp.record(i=5, j=2)), _sender=player2)
        c2.play(play(f=sp.record(i=2, j=5), t=sp.record(i=0, j=6)), _sender=player1)
        c2.play(play(f=sp.record(i=5, j=2), t=sp.record(i=7, j=1)), _sender=player2)
        c2.threefold_repetition_claim(
            fullMove1=0,
            fullMove2=5,
            _sender=player1,
            _valid=False,
            _exception=sp.pair("NotSameMove", sp.record(fullMove=5)),
        )
        c2.threefold_repetition_claim(fullMove1=0, fullMove2=4, _sender=player1)
        sc.verify(c2.data.status == sp.variant.finished("draw"))
