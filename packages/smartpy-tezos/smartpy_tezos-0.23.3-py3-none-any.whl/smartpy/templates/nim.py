# Nim Game, https://en.wikipedia.org/wiki/Nim - Example for illustrative purposes only.

import smartpy as sp


@sp.module
def main():
    def vector(xs):
        m = {}
        k = 0
        for v in xs:
            m[k] = v
            k += 1
        return m

    class NimGame(sp.Contract):
        def __init__(self, size, bound, winnerIsLast):
            self.private.bound = bound
            self.private.winnerIsLast = winnerIsLast
            self.data.deck = vector(range(1, size + 1))
            self.data.size = size
            self.data.nextPlayer = 1
            self.data.claimed = False
            self.data.winner = 0

        @sp.entrypoint
        def remove(self, params):
            assert params.cell >= 0
            assert params.cell < self.data.size
            assert params.k >= 1
            match self.private.bound:
                case Some(bound):
                    assert params.k <= bound
            assert params.k <= self.data.deck[params.cell]
            self.data.deck[params.cell] = self.data.deck[params.cell] - params.k
            self.data.nextPlayer = 3 - self.data.nextPlayer

        @sp.entrypoint
        def claim(self, params):
            assert sum(self.data.deck.values()) == 0
            assert not self.data.claimed
            self.data.claimed = True
            if self.private.winnerIsLast:
                self.data.winner = 3 - self.data.nextPlayer
            else:
                self.data.winner = self.data.nextPlayer
            assert params.winner == self.data.winner


# Tests
if "main" in __name__:

    @sp.add_test()
    def test():
        scenario = sp.test_scenario("Nim")
        scenario.h1("Nim game")
        # define a contract
        c1 = main.NimGame(size=5, bound=sp.Some(2), winnerIsLast=False)
        # show its representation
        scenario.h2("Contract")
        scenario += c1
        scenario.h2("Message execution")
        scenario.h3("A first move")
        c1.remove(cell=2, k=1)
        scenario.h3("A second move")
        c1.remove(cell=2, k=2)
        scenario.h3("An illegal move")
        c1.remove(cell=2, k=1, _valid=False)
        scenario.h3("Another illegal move")

        c1.claim(winner=1, _valid=False)
        scenario.h3("A third move")
        c1.remove(cell=1, k=2)
        scenario.h3("More moves")
        c1.remove(cell=0, k=1)
        c1.remove(cell=3, k=1)
        c1.remove(cell=3, k=1)
        c1.remove(cell=3, k=2)
        c1.remove(cell=4, k=1)
        c1.remove(cell=4, k=2)
        scenario.h3("A failed attempt to claim")
        c1.claim(winner=1, _valid=False)
        scenario.h3("A last removal")
        c1.remove(cell=4, k=2)
        scenario.h3("And a final claim")
        c1.claim(winner=1)
        scenario.p("The winner is").show(c1.data.winner)
