# Multiple Nim Games - Example for illustrative purposes only.

# Instead of defining a single NimGame per contract,
# we define a contract for multiple games.

import smartpy as sp


@sp.module
def main():
    def rangeMap(params):
        (a, b) = params
        r = {}
        for i in range(a, b):
            r[i - a] = i
        return r

    class NimMultipleGame(sp.Contract):
        def __init__(self):
            self.data.games = {}
            self.data.nbGames = 0

        @sp.entrypoint
        def build(self, params):
            size = params.size
            bound = params.bound
            lastWins = False
            game = sp.record(
                deck=rangeMap((1, size + 1)),
                size=size,
                nextPlayer=1,
                claimed=False,
                winner=0,
                bound=bound,
                lastWins=lastWins,
            )
            self.data.games[self.data.nbGames] = game
            self.data.nbGames += 1

        @sp.entrypoint
        def remove(self, params):
            gameId = params.gameId
            game = self.data.games[gameId]
            cell = params.cell
            k = params.k
            assert 0 <= cell
            assert cell < game.size
            assert 1 <= k
            assert k <= game.bound
            assert k <= game.deck[cell]
            game.deck[cell] = game.deck[cell] - k
            game.nextPlayer = 3 - game.nextPlayer
            self.data.games[gameId] = game

        @sp.entrypoint
        def claim(self, params):
            gameId = params.gameId
            game = self.data.games[gameId]
            assert sum(game.deck.values()) == 0
            game.claimed = True
            if game.lastWins:
                game.winner = 3 - game.nextPlayer
            else:
                game.winner = game.nextPlayer
            self.data.games[gameId] = game


# Tests
@sp.add_test()
def test():
    scenario = sp.test_scenario("NimGames")
    # define a contract
    c1 = main.NimMultipleGame()
    # show its representation
    scenario.h1("Nim games")
    scenario.h2("Contract")
    scenario += c1
    scenario.h2("First: define a few games with build")
    for size in range(5, 8):
        c1.build(size=size, bound=2)
    scenario.h2("Message execution")
    scenario.h3("A first move")
    c1.remove(gameId=0, cell=2, k=1)
    scenario.h3("A second move")
    c1.remove(gameId=0, cell=2, k=2)
    scenario.h3("An illegal move")
    c1.remove(gameId=0, cell=2, k=1, _valid=False)
    scenario.h3("Another illegal move")
    c1.claim(gameId=1, _valid=False)
    scenario.h3("A third move")
    c1.remove(gameId=0, cell=1, k=2)
    scenario.h3("More moves")
    c1.remove(gameId=0, cell=0, k=1)
    c1.remove(gameId=0, cell=3, k=1)
    c1.remove(gameId=0, cell=3, k=1)
    c1.remove(gameId=0, cell=3, k=2)
    c1.remove(gameId=0, cell=4, k=1)
    c1.remove(gameId=0, cell=4, k=2)
    scenario.h3("A failed attempt to claim")
    c1.claim(gameId=0, _valid=False)
    scenario.h3("A last removal")
    c1.remove(gameId=0, cell=4, k=2)
    scenario.h3("And a final claim")
    c1.claim(gameId=0)
