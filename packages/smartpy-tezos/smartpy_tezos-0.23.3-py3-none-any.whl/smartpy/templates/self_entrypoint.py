import smartpy as sp


@sp.module
def main():
    class A(sp.Contract):
        @sp.entrypoint
        def ep1(self, param: sp.string):
            pass

        @sp.entrypoint
        def ep2(self, param: sp.contract[sp.timestamp]):
            pass

    class B(sp.Contract):
        def __init__(self, a):
            self.data.a = a

        @sp.entrypoint
        def ep3(self, param: sp.bool):
            ep2 = sp.contract(
                sp.contract[sp.timestamp], self.data.a, entrypoint="ep2"
            ).unwrap_some()

            ep4 = sp.self_entrypoint("ep4")
            sp.cast(ep4, sp.contract[sp.timestamp])

            sp.transfer(ep4, sp.mutez(0), ep2)

        @sp.entrypoint
        def ep4(self, result: sp.timestamp):
            pass

    class Unrelated(sp.Contract):
        def __init__(self):
            self.data.x = "abc"


@sp.add_test()
def test():
    scenario = sp.test_scenario("test")
    a = main.A()
    scenario += a
    b = main.B(a=a.address)
    scenario += b
    b.ep3(True)
    scenario += main.Unrelated()
