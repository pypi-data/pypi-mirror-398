import smartpy as sp


@sp.module
def main():
    class MyContract(sp.Contract):
        def __init__(self, alice, bob):
            self.data.x = 2
            self.data.y = "aaa"
            self.data.z = 0
            self.data.alice = alice
            self.data.bob = bob

        @sp.private(with_storage="read-write", with_operations=True)
        def a(self, params):
            sp.cast(params, sp.nat)
            sp.send(self.data.alice, sp.mul(params, sp.tez(1)))
            sp.send(self.data.bob, sp.tez(2))
            self.data.x += 1
            return params * self.data.x

        @sp.entrypoint
        def f(self):
            self.data.z = self.a(10) + self.a(5)

        @sp.entrypoint
        def g(self):
            self.data.z = self.a(6)


alice = sp.test_account("alice").address
bob = sp.test_account("bob").address


@sp.add_test()
def test():
    scenario = sp.test_scenario("Sub")
    c1 = main.MyContract(alice, bob)
    c1.set_initial_balance(sp.tez(1000))
    scenario += c1
    c1.f()
    scenario.verify(c1.data == sp.record(x=4, z=55, y="aaa", alice=alice, bob=bob))
