import smartpy as sp


@sp.module
def main():
    class C1(sp.Contract):
        def __init__(self):
            self.data.x = None
            self.data.y = None

        @sp.entrypoint
        def auto_call(self):
            sp.transfer(sp.ticket(1, 43), sp.tez(0), sp.self_entrypoint("run"))

        @sp.entrypoint
        def run(self, params):
            sp.cast(params, sp.ticket[sp.int])
            (ticket_data, copy) = sp.read_ticket(params)
            self.data.y = sp.Some(sp.ticket("abc", 42))
            (t1, t2) = sp.split_ticket(
                copy,
                ticket_data.amount / 3,
                sp.as_nat(ticket_data.amount - ticket_data.amount / 3),
            )
            self.data.x = sp.Some(sp.join_tickets(t2, t1))

        @sp.entrypoint
        def run2(self, params):
            sp.cast(params, sp.record(t=sp.ticket[int], x=int))
            record(x, t).match = params
            assert x == 42
            (ticket_data, copy) = sp.read_ticket(t)
            self.data.y = sp.Some(sp.ticket("abc", 42))
            (t1, t2) = sp.split_ticket(
                copy,
                ticket_data.amount / 3,
                sp.as_nat(ticket_data.amount - ticket_data.amount / 3),
            )
            self.data.x = sp.Some(sp.join_tickets(t2, t1))

    class C2(sp.Contract):
        def __init__(self, t: sp.ticket[sp.nat]):
            self.data.t = t

        @sp.entrypoint
        def run(self):
            with sp.modify_record(self.data) as data:
                (ticket_data, copy) = sp.read_ticket(data.t)
                assert ticket_data.contents == 42
                (t1, t2) = sp.split_ticket(
                    copy, ticket_data.amount / 2, ticket_data.amount / 2
                )
                data.t = sp.join_tickets(t2, t1)

    class C3(sp.Contract):
        def __init__(self):
            self.data.m = sp.cast({}, sp.map[int, sp.ticket[int]])

        @sp.entrypoint
        def ep1(self):
            with sp.modify_record(self.data) as d:
                (t, m) = sp.get_and_update(42, None, d.m)
                d.m = m

    class C4(sp.Contract):
        def __init__(self):
            self.data.m = sp.cast({}, sp.map[int, sp.ticket[int]])
            self.data.x = 0

        @sp.entrypoint
        def ep1(self):
            with sp.modify_record(self.data) as data:
                (t, m) = sp.get_and_update(42, None, data.m)
                data.m = m
                data.x = 0

        @sp.entrypoint
        def ep2(self, cb):
            with sp.modify_record(self.data) as data:
                t1 = sp.ticket("a", 1)
                t2 = sp.ticket("b", 2)
                sp.transfer((t1, t2), sp.mutez(0), cb)


# Check that ticket cannot be used twice
@sp.module
def m2():
    class C(sp.Contract):
        @sp.entrypoint
        def ep(self, t):
            sp.cast(t, sp.ticket[sp.unit])
            x = t
            y = t


@sp.module
def m3():
    class C(sp.Contract):
        @sp.entrypoint
        def ep(self, tickets):
            sp.cast(tickets, sp.pair[sp.ticket[sp.unit], sp.ticket[sp.unit]])
            (t1, t2) = tickets
            x = t1
            y = sp.join_tickets(t2, t1)


# Check that trace is possible
@sp.module
def m4():
    class C(sp.Contract):
        @sp.entrypoint
        def ep(self, t):
            sp.cast(t, sp.ticket[sp.unit])
            sp.trace(t)  # Trace is not duplicating the ticket
            x = t  # Thus we can use it again
            sp.trace(t)  # We can trace it again
            sp.trace(x)  # We can trace it in x too


def expect_type_error(func, failure, *args, **kwargs):
    try:
        func(*args, **kwargs)
    except sp.TypeError_ as e:
        assert e.message == failure, f"Expected failure: {failure}, got: {e.message}"
    else:
        raise "Should have failed"


# Test join_tickets
@sp.module
def m5():
    class C(sp.Contract):
        def __init__(self):
            self.data.x = None

        @sp.entrypoint
        def ep(self, tickets):
            sp.cast(tickets, sp.pair[sp.ticket[sp.unit], sp.ticket[sp.unit]])
            (t1, t2) = tickets
            sp.trace(t1)
            sp.trace(t2)
            self.data.x = sp.Some(sp.join_tickets(t2, t1))
            sp.trace(self.data.x)


@sp.add_test()
def test():
    s = sp.test_scenario("Ticket")
    c = main.C1()
    s += c
    c.auto_call()
    t = sp.test_ticket(c.address, 5, 6)
    c.run(t)
    s.verify(sp.fst(sp.read_ticket_raw(c.data.x.unwrap_some())).amount == 6)

    s += main.C2(t)
    s += main.C3()
    s += main.C4()

    expect_type_error(
        m2.C,
        "Variable '__parameter__' of type sp.ticket[sp.unit] cannot be used twice because it contains a ticket.",
    )
    expect_type_error(
        m3.C,
        "Variable 't1' of type sp.ticket[sp.unit] cannot be used twice because it contains a ticket.",
    )
    s += m4.C()

    c = m5.C()
    s += c
    c.ep((sp.test_ticket(c.address, sp.unit, 3), sp.test_ticket(c.address, sp.unit, 4)))
    s.verify(sp.fst(sp.read_ticket_raw(c.data.x.unwrap_some())).amount == 7)
