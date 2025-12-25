import smartpy as sp


@sp.module
def main():
    class Parent(sp.Contract):
        @sp.entrypoint()
        def ep(self):
            pass

    class Factory(sp.Contract):
        @sp.entrypoint
        def create(self):
            _ = sp.create_contract(Parent, None, sp.tez(4), ())


@sp.add_test()
def testHierarchy():
    sc = sp.test_scenario("Factory")
    f = main.Factory()
    sc += f
    f.create(_amount=sp.tez(5))
    sc.verify(f.balance == sp.tez(1))
    f.create(_valid=False)
