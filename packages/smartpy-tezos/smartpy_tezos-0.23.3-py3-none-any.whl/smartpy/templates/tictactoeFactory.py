# TicTacToe Factory - Example for illustrative purposes only.

import smartpy as sp


@sp.module
def main():
    class TicTacToe(sp.Contract):
        def __init__(self, admin):
            self.data.admin = admin
            self.data.paused = False
            self.data.boards = sp.big_map()
            self.data.metaData = {}

        @sp.entrypoint
        def build(self, params):
            sp.cast(params.game, sp.string)
            assert not self.data.paused or sp.sender == self.data.admin
            assert not self.data.boards.contains(params.game)
            self.data.boards[params.game] = sp.record(
                player1=params.player1,
                player2=params.player2,
                nbMoves=0,
                winner=0,
                draw=False,
                deck={
                    0: {0: 0, 1: 0, 2: 0},
                    1: {0: 0, 1: 0, 2: 0},
                    2: {0: 0, 1: 0, 2: 0},
                },
                nextPlayer=1,
                metaData={},
            )

        @sp.entrypoint
        def deleteGame(self, params):
            assert sp.sender == self.data.admin
            del self.data.boards[params.game]

        @sp.entrypoint
        def setPause(self, params):
            assert sp.sender == self.data.admin
            self.data.paused = params

        @sp.entrypoint
        def setMetaData(self, params):
            assert sp.sender == self.data.admin
            sp.cast(params.name, sp.string)
            sp.cast(params.value, sp.string)
            self.data.metaData[params.name] = params.value

        @sp.entrypoint
        def setGameMetaData(self, params):
            game = self.data.boards[params.game]
            assert sp.sender == self.data.admin or sp.sender == game.player1
            sp.cast(params.name, sp.string)
            sp.cast(params.value, sp.string)
            game.metaData[params.name] = params.value

        @sp.entrypoint
        def play(self, params):
            assert not self.data.paused
            game = self.data.boards[params.game]
            assert game.winner == 0 and not game.draw
            assert params.i >= 0 and params.i < 3
            assert params.j >= 0 and params.j < 3
            assert params.move == game.nextPlayer
            assert game.deck[params.i][params.j] == 0
            if params.move == 1:
                assert sp.sender == game.player1
            else:
                assert sp.sender == game.player2
            game.nextPlayer = 3 - game.nextPlayer
            game.deck[params.i][params.j] = params.move
            game.nbMoves += 1
            game.winner = self.checkLine(
                sp.record(winner=game.winner, line=game.deck[params.i])
            )
            game.winner = self.checkLine(
                sp.record(
                    winner=game.winner,
                    line={
                        0: game.deck[0][params.j],
                        1: game.deck[1][params.j],
                        2: game.deck[2][params.j],
                    },
                )
            )
            game.winner = self.checkLine(
                sp.record(
                    winner=game.winner,
                    line={0: game.deck[0][0], 1: game.deck[1][1], 2: game.deck[2][2]},
                )
            )
            game.winner = self.checkLine(
                sp.record(
                    winner=game.winner,
                    line={0: game.deck[0][2], 1: game.deck[1][1], 2: game.deck[2][0]},
                )
            )
            if game.nbMoves == 9 and game.winner == 0:
                game.draw = True
            self.data.boards[params.game] = game

        @sp.private()
        def checkLine(self, winner, line):
            winner_ = winner
            if line[0] != 0 and line[0] == line[1] and line[0] == line[2]:
                winner_ = line[0]
            return winner_


# Tests
if "main" in __name__:

    @sp.add_test()
    def test():
        # define a contract
        admin = sp.test_account("Admin")
        alice = sp.test_account("Alice")
        bob = sp.test_account("Robert")

        scenario = sp.test_scenario("TicTacToeFactory")
        c1 = main.TicTacToe(admin.address)

        scenario.h1("Tic-Tac-Toe Games")
        # show its representation
        scenario.h2("A sequence of interactions with a winner")
        scenario += c1
        scenario.h2("Message execution")
        scenario.h3("Building a contract")

        g1 = "game 1"
        c1.build(game=g1, player1=alice.address, player2=bob.address)

        scenario.h3("A first move in the center")
        c1.play(game=g1, i=1, j=1, move=1, _sender=alice)

        g2 = "game 2"
        c1.build(game=g2, player1=alice.address, player2=bob.address)
        c1.deleteGame(game=g2, _sender=admin)

        c1.setMetaData(name="toto", value="titi", _sender=admin)

        c1.setGameMetaData(game=g1, name="toto", value="titi", _sender=alice)
        c1.setGameMetaData(game=g1, name="toto2", value="titi2", _sender=admin)
