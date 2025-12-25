# Jingle Bells - Example for illustrative purposes only.

import smartpy as sp


@sp.module
def main():
    lyrics = {
        0: "Dashing through the snow",
        1: "In a one-horse open sleigh",
        2: "O'er the fields we go",
        3: "Laughing all the way",
        4: "",
        5: "Bells on bob tail ring",
        6: "Making spirits bright",
        7: "What fun it is to ride and sing",
        8: "A sleighing song tonight!",
        9: "",
        10: "Jingle bells, jingle bells,",
        11: "Jingle all the way.",
        12: "Oh! what fun it is to ride",
        13: "In a one-horse open sleigh.",
        14: "",
        15: "Jingle bells, jingle bells,",
        16: "Jingle all the way;",
        17: "Oh! what fun it is to ride",
        18: "In a one-horse open sleigh.",
    }

    class JingleBells(sp.Contract):
        def __init__(self):
            self.private.lyrics = lyrics
            self.data.rules = [
                "Please sing as much as you wish!",
                "Happy Holidays from the SmartPy team!",
            ]
            self.data.played = 0
            self.data.verse = 0
            self.data.current = ""

        @sp.entrypoint
        def sing(self, params):
            for i in range(0, params.verses):
                if self.data.verse == len(lyrics):
                    self.data.played += 1
                    self.data.current = ""
                    self.data.verse = 0
                if self.data.current != "":
                    self.data.current += "\n"
                self.data.current += self.private.lyrics[self.data.verse]
                self.data.verse += 1


if "main" in __name__:

    @sp.add_test()
    def test():
        scenario = sp.test_scenario("JingleBells")
        c1 = main.JingleBells()
        scenario.h1("Jingle Bells")
        scenario += c1
        for i in range(0, 10):
            c1.sing(verses=1)
        c1.sing(verses=6)
        c1.sing(verses=100)
