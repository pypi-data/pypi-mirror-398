# Test empty data structures, in storage and in entrypoints.

import smartpy as sp


@sp.module
def main():
    class C(sp.Contract):
        def __init__(self):
            self.data.m1 = {}
            self.data.m2 = {"a": "b"}
            self.data.l1 = []
            self.data.l2 = ["c"]
            self.data.o1 = None
            # self.data.o2 = sp.Some('d') # This should be uncommented. See #41.

        @sp.entrypoint
        def ep1(self):
            self.data.m1 = {"e": "f"}
            self.data.l1 = ["g"]
            self.data.o1 = sp.Some("h")

        @sp.entrypoint
        def ep2(self):
            self.data.m2 = {}
            self.data.l2 = []
            # self.data.o2 = None


@sp.add_test()
def test():
    scenario = sp.test_scenario("test")
    c = main.C()
    scenario.h1("Empty")
    scenario += c
    c.ep1()
    c.ep2()
