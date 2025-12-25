# Check DFS, calling other contracts - Example for illustrative purposes only.

import smartpy as sp


@sp.module
def main():
    class Check_dfs(sp.Contract):
        def __init__(self):
            self.data.steps = ""
            self.data.conclusion = ""

        @sp.entrypoint
        def a(self):
            self.data.steps += ".a"
            sp.transfer((), sp.mutez(0), sp.self_entrypoint("aa"))

        @sp.entrypoint
        def aa(self):
            self.data.steps += ".aa"

        @sp.entrypoint
        def b(self):
            self.data.steps += ".b"
            if self.data.steps == "check.a.b":
                self.data.conclusion = "BFS"
            else:
                self.data.conclusion = "DFS"

        @sp.entrypoint
        def check(self):
            self.data.steps = "check"
            self.data.conclusion = ""
            sp.transfer((), sp.mutez(0), sp.self_entrypoint("a"))
            sp.transfer((), sp.mutez(0), sp.self_entrypoint("b"))


@sp.add_test()
def test():
    scenario = sp.test_scenario("dfs")
    scenario.h2("Depth first")
    check_dfs = main.Check_dfs()
    scenario += check_dfs
    check_dfs.check()
    scenario.verify(check_dfs.data.conclusion == "DFS")
