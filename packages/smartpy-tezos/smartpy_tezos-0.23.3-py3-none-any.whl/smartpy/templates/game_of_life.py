# Game of Life - Example for illustrative purposes only.
# In honor of John Conway

import smartpy as sp


@sp.module
def main():
    def board(size):
        b = {}
        for i in range(0, size):
            b[i] = {}
            for j in range(0, size):
                b[i][j] = 0
        return b

    class Game_of_life(sp.Contract):
        def __init__(self, size):
            self.private.size = size
            self.private.zero = board(size)
            self.data.board = {}

        @sp.entrypoint
        def reset(self):
            self.data.board = self.private.zero

        @sp.entrypoint
        def glider(self):
            self.data.board = self.private.zero
            x = self.private.size / 3
            self.data.board[x][x] = 1
            self.data.board[x + 1][x + 1] = 1
            self.data.board[x + 2][x - 1] = 1
            self.data.board[x + 2][x] = 1
            self.data.board[x + 2][x + 1] = 1

        @sp.entrypoint
        def bar(self):
            self.data.board = self.private.zero
            x = self.private.size / 2
            for k in range(0, self.private.size):
                self.data.board[x][k] = 1

        @sp.entrypoint
        def run(self):
            next = self.private.zero
            for i in range(0, self.private.size):
                for j in range(0, self.private.size):
                    sum = 0
                    for k in range(-1, 2):
                        if 0 <= i + k and i + k < self.private.size:
                            for l in range(-1, 2):
                                if 0 <= j + l and j + l < self.private.size:
                                    if k != 0 or l != 0:
                                        sum += self.data.board[i + k][j + l]
                    if self.data.board[i][j] == 0:
                        if sum == 3:
                            next[i][j] = 1
                    else:
                        if 2 <= sum and sum <= 3:
                            next[i][j] = 1
            self.data.board = next


if "main" in __name__:

    @sp.add_test()
    def test():
        scenario = sp.test_scenario("GameOfLife")
        c1 = main.Game_of_life(10)
        scenario.h1("Game of life")

        scenario += c1

        scenario.h2("Zero")
        c1.reset()

        scenario.h2("Glider")
        c1.glider()
        for i in range(0, 20):
            c1.run()

        scenario.h2("Horizontal Bar")
        c1.bar()
        for i in range(0, 18):
            c1.run()
