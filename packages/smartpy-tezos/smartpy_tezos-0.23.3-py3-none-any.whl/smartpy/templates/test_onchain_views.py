import smartpy as sp


@sp.module
def main():
    T: type = sp.record(
        now=sp.timestamp,
        level=sp.nat,
        amount=sp.mutez,
        balance=sp.mutez,
        chain_id=sp.chain_id,
        sender=sp.address,
        source=sp.address,
        total_voting_power=sp.nat,
    )

    class Lib(sp.Contract):
        def __init__(self):
            self.data.x = 10
            self.data.z = sp.nat(42)

        @sp.onchain_view()
        def view1(self):
            return sp.record(z=self.data.z, self_addr=sp.self_address)

        @sp.onchain_view()
        def view2(self):
            return self.data.z

        @sp.onchain_view()
        def view3(self, a):
            return self.data.x * a

    class C(sp.Contract):
        def __init__(self, c):
            self.data.result = None
            self.data.result2 = None
            self.data.contract = c
            self.data.self_addr = None
            self.data.self_addr_2 = None
            self.data.self_addr_3 = None

        # TODO: activate when view naming is possible
        # @sp.onchain_view(name="a_really_good_name")
        @sp.onchain_view
        def view(self):
            return sp.record(
                now=sp.now,
                level=sp.level,
                amount=sp.amount,
                balance=sp.balance,
                chain_id=sp.chain_id,
                sender=sp.sender,
                source=sp.source,
                total_voting_power=sp.total_voting_power,
            )

        @sp.entrypoint
        def store(self):
            self.data.self_addr = sp.Some(sp.self_address)
            res = sp.view(
                "view1",
                self.data.contract,
                (),
                sp.record(z=sp.nat, self_addr=sp.address),
            ).unwrap_some(error="Invalid view")

            # TODO: activate when view naming is possible
            # self.data.result2 = sp.view("a_really_good_name", sp.self_address, (), T)
            self.data.result2 = sp.view("view", sp.self_address, (), T)
            self.data.result = sp.Some(res.z)
            self.data.self_addr_2 = sp.Some(res.self_addr)
            self.data.self_addr_3 = sp.Some(sp.self_address)
            assert self.data.self_addr == self.data.self_addr_3
            assert self.data.self_addr_2 == sp.Some(self.data.contract)

        @sp.entrypoint
        def check_view(self):
            """Check view, possibly missing but not failing"""
            _ = sp.view("abc", sp.self_address, (), sp.unit)

        @sp.entrypoint
        def failing_entrypoint(self):
            raise "This is a failure"


@sp.add_test()
def test():
    s = sp.test_scenario("Lib")

    alice = sp.test_account("alice")

    lib = main.Lib()
    s += lib
    s.verify(lib.view2() == 42)
    s.verify(lib.view3(2) == 20)

    lib2 = main.Lib()
    s += lib2
    s.verify(lib2.view2() == 42)
    s.verify(lib2.view3(2) == 20)

    c = main.C(lib.address)
    c.set_initial_balance(sp.mutez(1234))
    s += c

    if s.simulation_mode() is sp.SimulationMode.MOCKUP:
        s.p("timestamps not implemented in mockups")
        return

    # This fails in Hangzhou
    c.store(
        (),
        _now=sp.timestamp(1),
        _level=101,
        _amount=sp.mutez(100),
        _chain_id=sp.chain_id_cst("0x9caecab9"),
        _source=alice,
        _sender=alice,
        _voting_powers={sp.key_hash("KT1TezoooozzSmartPyzzSTATiCzzzwwBFA1"): 10},
    )

    s.show(c.data.result2.unwrap_some())

    s.verify(
        c.data.result2.unwrap_some()
        == sp.record(
            now=sp.timestamp(1),
            level=101,
            amount=sp.mutez(0),
            balance=sp.mutez(1334),
            chain_id=sp.chain_id_cst("0x9caecab9"),
            total_voting_power=10,
            sender=c.address,
            source=alice.address,
        )
    )

    c.store(
        _now=sp.timestamp(2),
        _level=102,
        _amount=sp.mutez(150),
        _chain_id=sp.chain_id_cst("0x9caecab9"),
        _source=alice,
        _sender=c.address,
        _voting_powers={sp.key_hash("KT1TezoooozzSmartPyzzSTATiCzzzwwBFA1"): 10},
    )

    s.verify(
        c.data.result2.unwrap_some()
        == sp.record(
            now=sp.timestamp(2),
            level=102,
            amount=sp.mutez(0),
            balance=sp.mutez(1484),
            chain_id=sp.chain_id_cst("0x9caecab9"),
            total_voting_power=10,
            sender=c.address,
            source=alice.address,
        )
    )

    c.failing_entrypoint(
        _valid=False,
        _now=sp.timestamp(3),
        _level=103,
        _amount=sp.mutez(100),
        _chain_id=sp.chain_id_cst("0x9caecab9"),
        _source=alice,
        _sender=c.address,
        _voting_powers={sp.key_hash("KT1TezoooozzSmartPyzzSTATiCzzzwwBFA1"): 10},
    )

    c.store(
        _amount=sp.mutez(200),
        _source=alice,
        _sender=alice,
    )

    s.verify(
        c.data.result2.unwrap_some()
        == sp.record(
            now=sp.timestamp(2),
            level=102,
            amount=sp.mutez(0),
            balance=sp.mutez(1684),
            chain_id=sp.chain_id_cst("0x9caecab9"),
            total_voting_power=10,
            sender=c.address,
            source=alice.address,
        )
    )

    c.store(
        _source=alice,
        _sender=alice,
    )

    s.verify(
        c.data.result2.unwrap_some()
        == sp.record(
            now=sp.timestamp(2),
            level=102,
            amount=sp.mutez(0),
            balance=sp.mutez(1684),
            chain_id=sp.chain_id_cst("0x9caecab9"),
            total_voting_power=10,
            sender=c.address,
            source=alice.address,
        )
    )

    view_result = s.compute(c.view(), source=alice, sender=c.address)

    s.verify(
        view_result
        == sp.record(
            now=sp.timestamp(2),
            level=102,
            amount=sp.mutez(0),
            balance=sp.mutez(1684),
            chain_id=sp.chain_id_cst("0x9caecab9"),
            total_voting_power=10,
            sender=c.address,
            source=alice.address,
        )
    )

    s.verify(
        s.compute(c.view(), source=alice, sender=c.address, now=sp.timestamp(42))
        == sp.record(
            now=sp.timestamp(42),
            level=102,
            amount=sp.mutez(0),
            balance=sp.mutez(1684),
            chain_id=sp.chain_id_cst("0x9caecab9"),
            total_voting_power=10,
            sender=c.address,
            source=alice.address,
        )
    )

    s.verify(s.compute(lib.view1()) == sp.record(z=42, self_addr=lib.address))
