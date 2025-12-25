import smartpy as sp


@sp.module
def main():
    class Counter(sp.Contract):
        def __init__(self):
            self.data.x = 0

        @sp.entrypoint
        def incr(self):
            self.data.x += 1
            assert self.data.x <= 3

        @sp.entrypoint
        def set(self, x):
            self.data.x = x

    class B(sp.Contract):
        def __init__(self, counter_address):
            self.data.counter_address = counter_address
            self.data.last = ""

        @sp.entrypoint
        def ep(self, last):
            c_incr = sp.contract(
                sp.unit, self.data.counter_address, entrypoint="incr"
            ).unwrap_some()
            sp.transfer((), sp.mutez(0), c_incr)
            self.data.last = last

    class Factory(sp.Contract):
        def __init__(self):
            self.data.created = None

        @sp.entrypoint
        def create(self):
            self.data.created = sp.Some(
                sp.create_contract(Counter, None, sp.mutez(0), sp.record(x=0))
            )

        @sp.entrypoint
        def set(self, x):
            created = self.data.created.unwrap_some()
            contract = sp.contract(sp.int, created, entrypoint="set")
            sp.transfer(x, sp.tez(0), contract.unwrap_some())

        @sp.entrypoint
        def incr(self):
            created = self.data.created.unwrap_some()
            contract = sp.contract(sp.unit, created, entrypoint="incr")
            sp.transfer((), sp.tez(0), contract.unwrap_some())


def run_test(label, f):
    try:
        f()
    except Exception as e:
        print(label)
        print(e)


# Tests
@sp.add_test()
def test():
    s = sp.test_scenario("s1")
    counter = main.Counter()
    s += counter

    b = main.B(counter.address)
    s += b

    # Simple failure, caught:
    counter.set(100)
    s.verify((counter.data.x == 100) & (b.data.last == ""))
    run_test("e1", lambda: counter.incr())
    s.verify((counter.data.x == 100) & (b.data.last == ""))

    # We can continue after failure:
    counter.set(0)
    s.verify((counter.data.x == 0) & (b.data.last == ""))
    b.ep("A")
    s.verify((counter.data.x == 1) & (b.data.last == "A"))

    # Failed transactions are rolled back:
    b.ep("B")
    s.verify((counter.data.x == 2) & (b.data.last == "B"))
    b.ep("C")
    s.verify((counter.data.x == 3) & (b.data.last == "C"))
    run_test("e2", lambda: b.ep("D"))
    s.verify((counter.data.x == 3) & (b.data.last == "C"))

    # Expected failure:
    counter.incr(_valid=False)
    s.verify((counter.data.x == 3) & (b.data.last == "C"))

    # Expected failure with specified exception:
    counter.incr(_valid=False, _exception="Assert failure: self.data.x <= 3")
    s.verify((counter.data.x == 3) & (b.data.last == "C"))

    if s.simulation_mode() is sp.SimulationMode.MOCKUP:
        s.p("mockups - TODO invalid lambda changes contract data")
    else:
        # Expecting a failure that doesn't happen:
        run_test("e3", lambda: counter.set(0, _valid=False))
        s.verify((counter.data.x == 3) & (b.data.last == "C"))

        # Expecting a failure with the wrong error message:
        run_test("e4", lambda: counter.incr(_valid=False, _exception="expected"))
        s.verify((counter.data.x == 3) & (b.data.last == "C"))

        # Illegal combination of arguments:
        run_test("e5", lambda: counter.incr(_valid=True, _exception="expected"))
        s.verify((counter.data.x == 3) & (b.data.last == "C"))

        # Illegal combination of arguments:
        run_test("e6", lambda: counter.incr(_valid=True, _exception="expected"))
        s.verify((counter.data.x == 3) & (b.data.last == "C"))

    # Similar behavior with dynamically created contracts
    factory = main.Factory()
    s += factory
    factory.create()
    b2 = main.B(factory.data.created.unwrap_some())
    s += b2

    factory.set(100)
    run_test("f1", lambda: factory.incr())

    # We can continue after failure:
    factory.set(0)
    b2.ep("A")
    s.verify(b2.data.last == "A")

    # Failed transactions are rolled back:
    b2.ep("B")
    s.verify(b2.data.last == "B")
    b2.ep("C")
    s.verify(b2.data.last == "C")
    run_test("e2", lambda: b2.ep("D"))
    s.verify(b2.data.last == "C")

    # Expected failure:
    factory.incr(_valid=False)
    s.verify(b2.data.last == "C")

    # Expected failure with specified exception:
    factory.incr(_valid=False, _exception="Assert failure: self.data.x <= 3")
    s.verify(b2.data.last == "C")

    if s.simulation_mode() is sp.SimulationMode.MOCKUP:
        s.p("mockups - TODO invalid lambda changes contract data")
    else:
        # Expecting a failure that doesn't happen:
        run_test("e3", lambda: factory.set(0, _valid=False))
        s.verify(b2.data.last == "C")

        # Expecting a failure with the wrong error message:
        run_test("e4", lambda: factory.incr(_valid=False, _exception="expected"))
        s.verify(b2.data.last == "C")


try:

    class C(sp.Contract):
        pass

except ModuleNotFoundError as e:
    assert (
        e.args[0]
        == "`sp.Contract` can only be accessed within a .spy file or a function decorated with @sp.module. Please refer to the SmartPy documentation for more information."
    )
