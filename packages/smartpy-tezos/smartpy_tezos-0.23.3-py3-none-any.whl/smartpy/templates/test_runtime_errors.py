import smartpy as sp


@sp.module
def main():
    sender = sp.sender
    source = sp.source
    x1 = sp.mutez(1) - sp.mutez(2)
    x2 = {}[42]
    x3 = {}.get(42, error="oops")

    class C1(sp.Contract):
        @sp.entrypoint
        def ep(self):
            pass

    class C2(sp.Contract):
        pass

    class Caller(sp.Contract):
        @sp.entrypoint
        def drain(self, dest, amount):
            c = sp.contract(sp.unit, dest).unwrap_some()
            sp.transfer((), amount, c)


def run_test(label, f):
    try:
        f()
    except Exception as e:
        print(label)
        print(e)


@sp.add_test()
def test():
    s = sp.test_scenario("s")
    run_test("l001", lambda: s.compute(sender))
    run_test("l002", lambda: s.compute(source))
    run_test("l003", lambda: s.compute(main.x1))
    run_test("l004", lambda: s.compute(main.x2))
    run_test("l005", lambda: s.compute(main.x3))

    caller = main.Caller()
    s += caller

    c1 = main.C1()
    s += c1
    run_test(
        "l006", lambda: caller.drain(sp.record(dest=c1.address, amount=sp.mutez(1000)))
    )

    c2 = main.C2()
    s += c2
    run_test(
        "l007", lambda: caller.drain(sp.record(dest=c2.address, amount=sp.mutez(0)))
    )

    run_test("l008", lambda: c1.ep(_exception="blah", _valid=True))
    run_test("l009", lambda: s.verify(False))
