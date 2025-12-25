import smartpy as sp
from smartpy.templates.chess import build_fen, main, play

if "main" in __name__:
    player1 = sp.test_account("player1")
    player2 = sp.test_account("player2")

    @sp.add_test()
    def test():
        sc = sp.test_scenario("Chess - Adams Michael vs Sedgwick David")
        c1 = main.Chess(player1.address, player2.address)

        sc.h1(
            " Adams, Michael vs. Sedgwick, David 1-0 London: Lloyds Bank op: 1984.??.??"
        )
        sc += c1
        # Adams, Michael vs. Sedgwick, David 1-0
        # London: Lloyds Bank op: 1984.??.??
        sc.verify(
            build_fen(c1) == "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        )
        c1.play(play(f=sp.record(i=1, j=4), t=sp.record(i=3, j=4)), _sender=player1)
        sc.verify(
            build_fen(c1)
            == "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
        )
        c1.play(play(f=sp.record(i=6, j=4), t=sp.record(i=5, j=4)), _sender=player2)
        sc.verify(
            build_fen(c1)
            == "rnbqkbnr/pppp1ppp/4p3/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2"
        )
        c1.play(play(f=sp.record(i=1, j=3), t=sp.record(i=3, j=3)), _sender=player1)
        sc.verify(
            build_fen(c1)
            == "rnbqkbnr/pppp1ppp/4p3/8/3PP3/8/PPP2PPP/RNBQKBNR b KQkq d3 0 2"
        )
        c1.play(play(f=sp.record(i=6, j=3), t=sp.record(i=4, j=3)), _sender=player2)
        sc.verify(
            build_fen(c1)
            == "rnbqkbnr/ppp2ppp/4p3/3p4/3PP3/8/PPP2PPP/RNBQKBNR w KQkq d6 0 3"
        )
        c1.play(play(f=sp.record(i=0, j=1), t=sp.record(i=1, j=3)), _sender=player1)
        sc.verify(
            build_fen(c1)
            == "rnbqkbnr/ppp2ppp/4p3/3p4/3PP3/8/PPPN1PPP/R1BQKBNR b KQkq - 1 3"
        )
        c1.play(play(f=sp.record(i=7, j=6), t=sp.record(i=5, j=5)), _sender=player2)
        sc.verify(
            build_fen(c1)
            == "rnbqkb1r/ppp2ppp/4pn2/3p4/3PP3/8/PPPN1PPP/R1BQKBNR w KQkq - 2 4"
        )
        c1.play(play(f=sp.record(i=3, j=4), t=sp.record(i=4, j=4)), _sender=player1)
        sc.verify(
            build_fen(c1)
            == "rnbqkb1r/ppp2ppp/4pn2/3pP3/3P4/8/PPPN1PPP/R1BQKBNR b KQkq - 0 4"
        )
        c1.play(play(f=sp.record(i=5, j=5), t=sp.record(i=6, j=3)), _sender=player2)
        sc.verify(
            build_fen(c1)
            == "rnbqkb1r/pppn1ppp/4p3/3pP3/3P4/8/PPPN1PPP/R1BQKBNR w KQkq - 1 5"
        )
        c1.play(play(f=sp.record(i=1, j=5), t=sp.record(i=3, j=5)), _sender=player1)
        sc.verify(
            build_fen(c1)
            == "rnbqkb1r/pppn1ppp/4p3/3pP3/3P1P2/8/PPPN2PP/R1BQKBNR b KQkq f3 0 5"
        )
        c1.play(play(f=sp.record(i=6, j=2), t=sp.record(i=4, j=2)), _sender=player2)
        sc.verify(
            build_fen(c1)
            == "rnbqkb1r/pp1n1ppp/4p3/2ppP3/3P1P2/8/PPPN2PP/R1BQKBNR w KQkq c6 0 6"
        )
        c1.play(play(f=sp.record(i=1, j=2), t=sp.record(i=2, j=2)), _sender=player1)
        sc.verify(
            build_fen(c1)
            == "rnbqkb1r/pp1n1ppp/4p3/2ppP3/3P1P2/2P5/PP1N2PP/R1BQKBNR b KQkq - 0 6"
        )
        c1.play(play(f=sp.record(i=7, j=1), t=sp.record(i=5, j=2)), _sender=player2)
        sc.verify(
            build_fen(c1)
            == "r1bqkb1r/pp1n1ppp/2n1p3/2ppP3/3P1P2/2P5/PP1N2PP/R1BQKBNR w KQkq - 1 7"
        )
        c1.play(play(f=sp.record(i=1, j=3), t=sp.record(i=2, j=5)), _sender=player1)
        sc.verify(
            build_fen(c1)
            == "r1bqkb1r/pp1n1ppp/2n1p3/2ppP3/3P1P2/2P2N2/PP4PP/R1BQKBNR b KQkq - 2 7"
        )
        c1.play(play(f=sp.record(i=4, j=2), t=sp.record(i=3, j=3)), _sender=player2)
        sc.verify(
            build_fen(c1)
            == "r1bqkb1r/pp1n1ppp/2n1p3/3pP3/3p1P2/2P2N2/PP4PP/R1BQKBNR w KQkq - 0 8"
        )
        c1.play(play(f=sp.record(i=2, j=2), t=sp.record(i=3, j=3)), _sender=player1)
        sc.verify(
            build_fen(c1)
            == "r1bqkb1r/pp1n1ppp/2n1p3/3pP3/3P1P2/5N2/PP4PP/R1BQKBNR b KQkq - 0 8"
        )
        c1.play(play(f=sp.record(i=6, j=5), t=sp.record(i=5, j=5)), _sender=player2)
        sc.verify(
            build_fen(c1)
            == "r1bqkb1r/pp1n2pp/2n1pp2/3pP3/3P1P2/5N2/PP4PP/R1BQKBNR w KQkq - 0 9"
        )
        c1.play(play(f=sp.record(i=0, j=5), t=sp.record(i=2, j=3)), _sender=player1)
        sc.verify(
            build_fen(c1)
            == "r1bqkb1r/pp1n2pp/2n1pp2/3pP3/3P1P2/3B1N2/PP4PP/R1BQK1NR b KQkq - 1 9"
        )
        c1.play(play(f=sp.record(i=7, j=5), t=sp.record(i=3, j=1)), _sender=player2)
        sc.verify(
            build_fen(c1)
            == "r1bqk2r/pp1n2pp/2n1pp2/3pP3/1b1P1P2/3B1N2/PP4PP/R1BQK1NR w KQkq - 2 10"
        )
        #     sc.verify(c1.data.board_state.check == True)
        c1.play(play(f=sp.record(i=0, j=2), t=sp.record(i=1, j=3)), _sender=player1)
        #     sc.verify(c1.data.board_state.check == False)
        sc.verify(
            build_fen(c1)
            == "r1bqk2r/pp1n2pp/2n1pp2/3pP3/1b1P1P2/3B1N2/PP1B2PP/R2QK1NR b KQkq - 3 10"
        )
        c1.play(play(f=sp.record(i=7, j=3), t=sp.record(i=5, j=1)), _sender=player2)
        sc.verify(
            build_fen(c1)
            == "r1b1k2r/pp1n2pp/1qn1pp2/3pP3/1b1P1P2/3B1N2/PP1B2PP/R2QK1NR w KQkq - 4 11"
        )
        c1.play(play(f=sp.record(i=0, j=6), t=sp.record(i=1, j=4)), _sender=player1)
        sc.verify(
            build_fen(c1)
            == "r1b1k2r/pp1n2pp/1qn1pp2/3pP3/1b1P1P2/3B1N2/PP1BN1PP/R2QK2R b KQkq - 5 11"
        )
        c1.play(play(f=sp.record(i=5, j=5), t=sp.record(i=4, j=4)), _sender=player2)
        sc.verify(
            build_fen(c1)
            == "r1b1k2r/pp1n2pp/1qn1p3/3pp3/1b1P1P2/3B1N2/PP1BN1PP/R2QK2R w KQkq - 0 12"
        )
        c1.play(play(f=sp.record(i=3, j=5), t=sp.record(i=4, j=4)), _sender=player1)
        sc.verify(
            build_fen(c1)
            == "r1b1k2r/pp1n2pp/1qn1p3/3pP3/1b1P4/3B1N2/PP1BN1PP/R2QK2R b KQkq - 0 12"
        )
        c1.play(
            play(f=sp.record(i=7, j=4), t=sp.record(i=7, j=6)), _sender=player2
        )  # Castle
        sc.verify(
            build_fen(c1)
            == "r1b2rk1/pp1n2pp/1qn1p3/3pP3/1b1P4/3B1N2/PP1BN1PP/R2QK2R w KQ - 1 13"
        )
        c1.play(play(f=sp.record(i=1, j=0), t=sp.record(i=2, j=0)), _sender=player1)
        c1.play(play(f=sp.record(i=3, j=1), t=sp.record(i=6, j=4)), _sender=player2)
        c1.play(play(f=sp.record(i=0, j=3), t=sp.record(i=1, j=2)), _sender=player1)
        c1.play(play(f=sp.record(i=7, j=5), t=sp.record(i=2, j=5)), _sender=player2)
        c1.play(play(f=sp.record(i=1, j=6), t=sp.record(i=2, j=5)), _sender=player1)
        c1.play(play(f=sp.record(i=5, j=2), t=sp.record(i=3, j=3)), _sender=player2)
        c1.play(play(f=sp.record(i=1, j=4), t=sp.record(i=3, j=3)), _sender=player1)
        c1.play(play(f=sp.record(i=5, j=1), t=sp.record(i=3, j=3)), _sender=player2)
        c1.play(
            play(f=sp.record(i=0, j=4), t=sp.record(i=0, j=2)), _sender=player1
        )  # O-O-O
        sc.verify(
            build_fen(c1)
            == "r1b3k1/pp1nb1pp/4p3/3pP3/3q4/P2B1P2/1PQB3P/2KR3R b - - 1 17"
        )
        c1.play(play(f=sp.record(i=6, j=3), t=sp.record(i=4, j=4)), _sender=player2)
        c1.play(
            play(f=sp.record(i=2, j=3), t=sp.record(i=6, j=7)), _sender=player1
        )  # check
        sc.verify(
            build_fen(c1) == "r1b3k1/pp2b1pB/4p3/3pn3/3q4/P4P2/1PQB3P/2KR3R b - - 0 18"
        )
        sc.verify(c1.data.board_state.check == True)
        c1.play(play(f=sp.record(i=7, j=6), t=sp.record(i=7, j=7)), _sender=player2)
        sc.verify(c1.data.board_state.check == False)
        c1.play(play(f=sp.record(i=0, j=2), t=sp.record(i=0, j=1)), _sender=player1)
        c1.play(play(f=sp.record(i=3, j=3), t=sp.record(i=3, j=7)), _sender=player2)
        c1.play(play(f=sp.record(i=1, j=3), t=sp.record(i=2, j=2)), _sender=player1)
        c1.play(play(f=sp.record(i=6, j=4), t=sp.record(i=5, j=5)), _sender=player2)
        c1.play(play(f=sp.record(i=2, j=5), t=sp.record(i=3, j=5)), _sender=player1)
        c1.play(play(f=sp.record(i=4, j=4), t=sp.record(i=3, j=2)), _sender=player2)
        c1.play(play(f=sp.record(i=2, j=2), t=sp.record(i=5, j=5)), _sender=player1)
        c1.play(play(f=sp.record(i=3, j=7), t=sp.record(i=5, j=5)), _sender=player2)
        c1.play(play(f=sp.record(i=6, j=7), t=sp.record(i=2, j=3)), _sender=player1)
        c1.play(play(f=sp.record(i=6, j=1), t=sp.record(i=4, j=1)), _sender=player2)
        c1.play(play(f=sp.record(i=1, j=2), t=sp.record(i=1, j=4)), _sender=player1)
        c1.play(play(f=sp.record(i=7, j=2), t=sp.record(i=6, j=3)), _sender=player2)
        c1.play(play(f=sp.record(i=0, j=7), t=sp.record(i=0, j=6)), _sender=player1)
        c1.play(play(f=sp.record(i=6, j=3), t=sp.record(i=7, j=4)), _sender=player2)
        c1.play(play(f=sp.record(i=0, j=3), t=sp.record(i=0, j=4)), _sender=player1)
        c1.play(play(f=sp.record(i=7, j=4), t=sp.record(i=6, j=5)), _sender=player2)
        sc.verify(
            build_fen(c1) == "r6k/p4bp1/4pq2/1p1p4/2n2P2/P2B4/1P2Q2P/1K2R1R1 w - - 6 27"
        )
        c1.play(play(f=sp.record(i=0, j=6), t=sp.record(i=2, j=6)), _sender=player1)
        c1.play(play(f=sp.record(i=7, j=0), t=sp.record(i=7, j=2)), _sender=player2)
        c1.play(play(f=sp.record(i=0, j=4), t=sp.record(i=0, j=6)), _sender=player1)
        c1.play(play(f=sp.record(i=3, j=2), t=sp.record(i=5, j=3)), _sender=player2)
        c1.play(play(f=sp.record(i=2, j=6), t=sp.record(i=6, j=6)), _sender=player1)
        c1.play(play(f=sp.record(i=5, j=3), t=sp.record(i=4, j=5)), _sender=player2)
        c1.play(play(f=sp.record(i=6, j=6), t=sp.record(i=4, j=6)), _sender=player1)
        c1.play(play(f=sp.record(i=7, j=2), t=sp.record(i=6, j=2)), _sender=player2)
        c1.play(play(f=sp.record(i=2, j=3), t=sp.record(i=4, j=5)), _sender=player1)
        c1.play(play(f=sp.record(i=5, j=4), t=sp.record(i=4, j=5)), _sender=player2)
        c1.play(
            play(f=sp.record(i=4, j=6), t=sp.record(i=4, j=7)), _sender=player1
        )  # Abandon
        sc.show(build_fen(c1))
        sc.verify(
            build_fen(c1) == "7k/p1r2b2/5q2/1p1p1p1R/5P2/P7/1P2Q2P/1K4R1 b - - 1 32"
        )
        sc.verify(c1.data.board_state.check == True)
        c1.play(play(f=sp.record(i=6, j=5), t=sp.record(i=4, j=7)), _sender=player2)
        c1.play(play(f=sp.record(i=1, j=4), t=sp.record(i=4, j=7)), _sender=player1)
        sc.show(build_fen(c1))
        c1.play(play(f=sp.record(i=5, j=5), t=sp.record(i=5, j=7)), _sender=player2)
        c1.play(play(f=sp.record(i=4, j=7), t=sp.record(i=5, j=7)), _sender=player1)
        c1.play(play(f=sp.record(i=6, j=2), t=sp.record(i=6, j=7)), _sender=player2)
        c1.play(play(f=sp.record(i=5, j=7), t=sp.record(i=7, j=5)), _sender=player1)
