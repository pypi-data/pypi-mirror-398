import smartpy as sp


@sp.module
def main():
    f_type: type = sp.lambda_(sp.unit, sp.unit, with_operations=True)

    class C1(sp.Contract):
        def __init__(self):
            self.data.x = sp.cast(None, sp.option[f_type])

        @sp.entrypoint
        def ep(self, to_):
            @sp.effects(with_operations=True)
            def f(param):
                (address, _) = param
                sp.send(address, sp.mutez(1))

            fp = sp.cast(f.apply(to_), f_type)
            self.data.x = sp.Some(fp)

        @sp.entrypoint
        def exec(self):
            _ = self.data.x.unwrap_some()()

    @sp.effects(with_operations=True)
    def send_to(to_):
        sp.send(to_, sp.tez(5))

    class C2(sp.Contract):
        @sp.entrypoint
        def my_entrypoint(self, alice):
            @sp.effects(with_operations=True)
            def f(au):
                (a, u) = au
                sp.cast(u, sp.unit)
                return send_to(a)

            _ = f.apply(alice)()

    class C3(sp.Contract):
        def __init__(self, alice):
            @sp.effects(with_operations=True)
            def f(au):
                (a, u) = au
                sp.cast(u, sp.unit)
                return send_to(a)

            self.data.f = f.apply(alice)

    c1: type = sp.pair[sp.nat, sp.unit]
    c2: type = sp.pair[sp.address, c1]
    c3: type = sp.pair[sp.bool, c2]
    c4: type = sp.pair[sp.int, c3]
    t_record: type = sp.record(a=sp.int, b=sp.bool, c=sp.address, d=sp.nat, e=sp.unit)

    @sp.effects(with_operations=True)
    def format_record(param):
        sp.cast(param, c4)
        (a, p2) = param
        (b, p3) = p2
        (c, p4) = p3
        (d, e) = p4
        return sp.cast(sp.record(a=a, b=b, c=c, d=d, e=e), t_record)

    class C4(sp.Contract):
        def __init__(self):
            self.data.value = sp.cast(None, sp.option[t_record])
            l1 = format_record.apply(1)
            l2 = l1.apply(True)
            l3 = l2.apply(sp.address("tz1Ke2h7sDdakHJQh8WX4Z372du1KChsksyU"))
            l4 = l3.apply(2)
            self.data.l1 = l1
            self.data.l2 = l2
            self.data.l3 = l3
            self.data.l4 = l4

        @sp.entrypoint
        def exec_l1(self):
            alice = sp.address("tz1Ke2h7sDdakHJQh8WX4Z372du1KChsksyU")
            self.data.value = sp.Some(self.data.l1((True, (alice, (2, ())))))

        @sp.entrypoint
        def exec_l2(self):
            alice = sp.address("tz1Ke2h7sDdakHJQh8WX4Z372du1KChsksyU")
            self.data.value = sp.Some(self.data.l2((alice, (2, ()))))

        @sp.entrypoint
        def exec_l3(self):
            self.data.value = sp.Some(self.data.l3((2, ())))

        @sp.entrypoint
        def exec_l4(self):
            self.data.value = sp.Some(self.data.l4())

    tl1: type = sp.lambda_(c3, sp.unit, with_operations=True, with_storage="read-write")
    tl2: type = sp.lambda_(c2, sp.unit, with_operations=True, with_storage="read-write")
    tl3: type = sp.lambda_(c1, sp.unit, with_operations=True, with_storage="read-write")
    tl4: type = sp.lambda_(
        sp.unit, sp.unit, with_operations=True, with_storage="read-write"
    )
    tls: type = sp.record(l1=tl1, l2=tl2, l3=tl3, l4=tl4)

    @sp.effects(with_storage="read-write", with_operations=True)
    def save_record(param):
        sp.cast(param, c4)
        (a, p2) = param
        (b, p3) = p2
        (c, p4) = p3
        (d, e) = p4
        self.data.value = sp.Some(sp.cast(sp.record(a=a, b=b, c=c, d=d, e=e), t_record))

    class C5(sp.Contract):
        def __init__(self):
            self.data.value = sp.cast(None, sp.option[t_record])

        @sp.entrypoint
        def build_and_exec(self, c):
            l1 = save_record.apply(1)
            l2 = l1.apply(True)
            l3 = l2.apply(sp.address("tz1Ke2h7sDdakHJQh8WX4Z372du1KChsksyU"))
            l4 = l3.apply(2)
            contract = sp.contract(tls, c, entrypoint="exec_lambdas").unwrap_some()
            sp.transfer(sp.record(l1=l1, l2=l2, l3=l3, l4=l4), sp.tez(0), contract)

    class C6(sp.Contract):
        def __init__(self):
            self.data.value = sp.cast(None, sp.option[t_record])

        @sp.entrypoint
        def exec_lambdas(self, param):
            sp.cast(param, tls)
            alice = sp.address("tz1Ke2h7sDdakHJQh8WX4Z372du1KChsksyU")
            param.l1((True, (alice, (2, ()))))
            param.l2((alice, (2, ())))
            param.l3((2, ()))
            param.l4()


@sp.add_test()
def test():
    s = sp.test_scenario("Test")

    c1 = main.C1()
    c1.set_initial_balance(sp.mutez(100))
    s += c1
    alice = sp.test_account("alice")
    c1.ep(alice.address)
    c1.exec()
    s.verify(c1.balance == sp.mutez(99))

    c2 = main.C2()
    c2.set_initial_balance(sp.tez(100))
    s += c2
    c2.my_entrypoint(alice.address)
    s.verify(c2.balance == sp.tez(95))

    c3 = main.C3(alice.address)
    s += c3

    c4 = main.C4()
    s += c4
    c4.exec_l1()
    c4.exec_l2()
    c4.exec_l3()
    c4.exec_l4()

    c5 = main.C5()
    s += c5
    c6 = main.C6()
    s += c6
    c5.build_and_exec(c6.address)
