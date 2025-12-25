import smartpy as sp


@sp.module
def main():
    class B(sp.Contract):
        def __init__(self):
            self.data.n = 0

        @sp.entrypoint
        def b(self):
            self.data.n += 1
            assert self.data.n < 2, ">= 2"

        @sp.entrypoint
        def fail(self):
            raise (
                "This is a very long error message with a looooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooong word."
            )

        @sp.entrypoint
        def do_nothing(self):
            pass

    class A(sp.Contract):
        def __init__(self):
            self.data.x = sp.cast(None, sp.option[sp.nat])
            self.data.y = sp.cast(None, sp.option[sp.nat])
            self.data.created = sp.cast(None, sp.option[sp.address])
            self.data.z = ""
            self.data.m = {
                sp.record(a="1", b="2"): sp.record(c="3", d=4),
                sp.record(a="2", b="3"): sp.record(c="a", d=42),
            }

        @sp.entrypoint
        def call_b(self, address):
            contract = sp.contract(sp.unit, address, entrypoint="b")
            sp.transfer((), sp.balance, contract.unwrap_some())

        @sp.entrypoint
        def emit(self, name):
            self.data.z += ", " + name
            sp.emit(name)
            sp.emit(name, with_type=False)
            sp.emit(name, tag="mytag")
            sp.emit(sp.record(name=name, b="XYZ"), tag="mytag2")
            sp.emit(sp.record(name=name, b="XYZ"), tag="mytag2", with_type=False)

        @sp.entrypoint
        def set_delegate(self, delegator):
            sp.set_delegate(delegator)
            sp.set_delegate(None)
            sp.set_delegate(delegator)

        @sp.entrypoint
        def create_contract(self, delegator, amount, data):
            self.data.created = sp.Some(sp.create_contract(B, delegator, amount, data))

        @sp.entrypoint
        def withdraw(self, amount):
            sp.send(sp.sender, amount)
            contract = sp.contract(sp.string, sp.sender, entrypoint="default_")
            sp.transfer("Test", sp.tez(0), contract.unwrap_some())


if "templates" not in __name__:

    @sp.add_test()
    def test():
        baker = sp.test_account("baker")
        baker2 = sp.test_account("baker2")
        voting_powers = {
            baker.public_key_hash: 42,
            baker2.public_key_hash: 10,
        }
        alice = sp.test_account("alice")
        sc = sp.test_scenario("MyContract")
        sc.h1("h1")
        sc.h2("h2")
        sc.h3("h3")
        sc.h4("h4")
        sc.p("p")

        sc.h2("Origination A")
        c1 = main.A()
        c1.set_initial_balance(sp.tez(5))
        c1.data.z = "Hello"
        sc += c1
        sc.verify(c1.data.z == "Hello")

        sc.h2("Origination B")
        c2 = main.B()
        sc += c2

        sc.h2("Call b")
        c1.call_b(c2.address, _amount=sp.tez(5))
        c1.call_b(c2.address, _amount=sp.tez(1), _valid=False)

        if sc.simulation_mode() is sp.SimulationMode.MOCKUP:
            sc.p("mockups - TODO set delegate")
        else:
            sc.h2("Set delegate")
            c1.set_delegate(
                sp.Some(baker.public_key_hash), _voting_powers=voting_powers
            )

        sc.h2("Show values")
        sc.show("test")
        sc.show(c1.data)
        sc.show(alice)

        sc.h2("Emit")
        c1.emit("alice", _sender=alice, _now=sp.timestamp(500), _voting_powers={})

        if sc.simulation_mode() is sp.SimulationMode.MOCKUP:
            sc.p("mockups - TODO set delegate with funds")
        else:
            sc.h2("Transfer to tz address")
            c1.withdraw(
                sp.tez(7), _sender=alice, _amount=sp.tez(8), _now=sp.timestamp(0)
            )

        sc.h2("Fail")
        c2.fail(
            _valid=False,
            _exception="This is a very long error message with a looooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooong word.",
        )

        if sc.simulation_mode() is sp.SimulationMode.MOCKUP:
            sc.p("mockups - TODO set delegate with funds")
        else:
            sc.h2("Create contract")
            c1.create_contract(
                sp.record(delegator=None, amount=sp.tez(8), data=sp.record(n=5)),
                _sender=alice,
                _amount=sp.tez(8),
            )
            c1.create_contract(
                sp.record(
                    delegator=sp.Some(baker.public_key_hash),
                    amount=sp.tez(0),
                    data=sp.record(n=0),
                ),
                _sender=alice,
                _amount=sp.tez(0),
            )

        sc.h2("Detailed context")
        c2.do_nothing(
            _sender=c1.address,
            _source=alice,
            _amount=sp.mutez(500),
            _voting_powers=voting_powers,
            _now=sp.timestamp(1000),
            _level=42,
            _chain_id=sp.chain_id_cst("0x9caecab9"),
        )

        sc.h2("Scenario verify")
        sc.verify(c2.data.n == 1)
        # sc.show("The following should fail:")
        # sc.verify(c2.data.n == 2)
        # sc.show("The following should fail:")
        # sc.verify("Expected to fail" == "True")

        x = sp.variant.Circle(0)
        sc.compute(x.unwrap_variant.Circle())

        now = sp.timestamp(1000)
        sc.verify_equal(sp.add_seconds(now, 1), sp.timestamp(1001))
        sc.verify_equal(sp.add_days(now, 1), sp.timestamp(1000 + 24 * 60 * 60))
