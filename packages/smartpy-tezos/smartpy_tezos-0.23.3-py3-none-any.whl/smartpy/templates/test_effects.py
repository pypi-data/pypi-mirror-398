import smartpy as sp


@sp.module
def main():
    class Sub(sp.Contract):
        def __init__(self):
            self.data.a = sp.nat(0)

        @sp.entrypoint
        def sub_incr(self):
            self.data.a = self.data.a + 1

        @sp.entrypoint
        def sub_double(self):
            self.data.a = 2 * self.data.a

    class Main(sp.Contract):
        def __init__(self, sub):
            self.private.sub = sub
            self.data.a = sp.nat(0)

        @sp.private(with_storage="read-write")
        def incr(self, x):
            self.data.a = self.data.a + 1
            return x + 1

        @sp.private(with_storage="read-write")
        def double(self, x):
            self.data.a = 2 * self.data.a
            return 2 * x

        @sp.private(with_operations=True)
        def sub_incr(self, params):
            sub_incr = sp.contract(
                sp.unit, params.sub, entrypoint="sub_incr"
            ).unwrap_some()
            sp.transfer((), sp.tez(0), sub_incr)
            return params.x + 1

        @sp.private(with_operations=True)
        def sub_double(self, params):
            sub_double = sp.contract(
                sp.unit, params.sub, entrypoint="sub_double"
            ).unwrap_some()
            sp.transfer((), sp.tez(0), sub_double)
            return 2 * params.x

        @sp.private(with_storage="read-write", with_operations=True)
        def sub_incr_both(self, params):
            sub_incr = sp.contract(
                sp.unit, params.sub, entrypoint="sub_incr"
            ).unwrap_some()
            sp.transfer((), sp.tez(0), sub_incr)
            self.data.a = self.data.a + 1
            return params.x + 1

        @sp.entrypoint
        def test_with_storage(self):
            self.data.a = 0
            assert self.incr(100) == 101
            assert self.data.a == 1

            self.data.a = 10
            assert self.double(100) == 200
            assert self.data.a == 20

            self.data.a = 10
            assert self.double(self.incr(100)) == 202
            assert self.data.a == 22

            self.data.a = 10
            assert self.double(100) + self.incr(1000) == 1201
            assert self.data.a == 22

            self.data.a = 10
            assert self.incr(1000) + self.double(100) == 1201
            assert self.data.a == 21

        @sp.entrypoint
        def test_sub_incr(self):
            self.data.a = 0
            assert self.sub_incr(sp.record(x=100, sub=self.private.sub)) == 101

        @sp.entrypoint
        def test_sub_incr_both(self):
            self.data.a = 0
            assert self.sub_incr_both(sp.record(x=100, sub=self.private.sub)) == 101
            assert self.data.a == 1

        @sp.entrypoint
        def test_sub_incr_store(self):
            self.data.a = self.sub_incr_both(sp.record(x=100, sub=self.private.sub))


@sp.add_test()
def test():
    s = sp.test_scenario("Effects")
    sub = main.Sub()
    s += sub
    main_ = main.Main(sub.address)
    s += main_
    main_.test_with_storage()

    s.verify(sub.data.a == 0)

    main_.test_sub_incr()
    s.verify(sub.data.a == 1)

    main_.test_sub_incr_both()
    s.verify(sub.data.a == 2)

    main_.test_sub_incr_store()
    s.verify(sub.data.a == 3)
    s.verify(main_.data.a == 101)


# tests for bad compilation
@sp.module
def init_effects():
    @sp.effects(with_exceptions=True)
    def hasExceptions(x):
        assert x > 0
        return x + 1

    class InitWithBadStatedEffect(sp.Contract):
        @sp.effects(with_exceptions=False)
        def __init__(self, x):
            # should fail to compile
            self.data.x = hasExceptions(x)


@sp.add_test()
def test_init_effects():
    try:
        _ = sp.test_scenario("TestInitEffects", init_effects)
    except sp.TypeError_ as e:
        print(e)
    else:
        assert False


@sp.module
def ep_effects():
    @sp.effects(with_mutez_overflow=True)
    def hasMutezOverflow(x: sp.mutez):
        return x + sp.mutez(1)

    class InitWithBadStatedEffect(sp.Contract):
        @sp.entrypoint(with_mutez_overflow=False)
        def ep(self, x):
            # should fail to compile
            self.data.x = hasMutezOverflow(x)


@sp.add_test()
def test_ep_effects():
    try:
        _ = sp.test_scenario("testEpEffects", ep_effects)
    except sp.TypeError_ as e:
        print(e)
    else:
        assert False


@sp.module
def ep_set_delegate():
    class InitWithBadStatedEffect(sp.Contract):
        @sp.entrypoint(with_operations=False)
        def doesSetDelegate(self, x):
            sp.set_delegate(sp.Some(x))


@sp.add_test()
def test_ep_set_delegate():
    try:
        _ = sp.test_scenario("testEpSetDelegate", ep_set_delegate)
    except sp.TypeError_ as e:
        print(e)
    else:
        assert False


@sp.module
def ep_emit():
    class InitWithBadStatedEffect(sp.Contract):
        @sp.entrypoint(with_operations=False)
        def doesEmit(self):
            sp.emit("hello")


@sp.add_test()
def test_ep_emit():
    try:
        _ = sp.test_scenario("testEpEmit", ep_emit)
    except sp.TypeError_ as e:
        print(e)
    else:
        assert False


@sp.module
def view_effects01():
    @sp.effects(with_mutez_underflow=True)
    def hasMutezUnderflow(x: sp.mutez):
        return x - sp.mutez(1)

    class InitWithBadStatedEffect(sp.Contract):
        @sp.effects(with_mutez_underflow=False)
        def __init__(self, x):
            # should fail to compile
            self.data.x = hasMutezUnderflow(x)


@sp.add_test()
def test_view_effects01():
    try:
        _ = sp.test_scenario("TestViewEffects01", view_effects01)
    except sp.TypeError_ as e:
        print(e)
    else:
        assert False


@sp.module
def view_effects02():
    class ViewWithBadStatedEffect(sp.Contract):
        def __init__(self, x):
            self.data.x = x

        @sp.private(with_storage="read-write")
        def _helper(self, x):
            self.data.x = x

        @sp.onchain_view
        def vw(self):
            # cannot call read-write func from view
            self._helper(2)
            return self.data.x + 1


@sp.add_test()
def test_view_effects02():
    try:
        _ = sp.test_scenario("TestViewEffects02", view_effects02)
    except sp.TypeError_ as e:
        print(e)
    else:
        assert False


@sp.module
def view_effects03():
    class Sub(sp.Contract):
        def __init__(self):
            self.data.a = sp.nat(0)

        @sp.entrypoint
        def sub_incr(self):
            self.data.a = self.data.a + 1

    class ViewWithBadStatedEffect(sp.Contract):
        def __init__(self, sub):
            self.private.sub = sub
            self.data.a = sp.nat(0)

        @sp.private(with_operations=True)
        def sub_incr(self, params):
            sub_incr = sp.contract(
                sp.unit, params.sub, entrypoint="sub_incr"
            ).unwrap_some()
            sp.transfer((), sp.tez(0), sub_incr)
            return params.x + 1

        @sp.onchain_view
        def test_sub_incr(self):
            return self.sub_incr(sp.record(x=100, sub=self.private.sub))


@sp.add_test()
def test_view_effects03():
    try:
        _ = sp.test_scenario("TestViewEffects03", view_effects03)
    except sp.TypeError_ as e:
        print(e)
    else:
        assert False


@sp.module
def view_effects04():
    class C(sp.Contract):
        def __init__(self, x):
            self.data.x = x

        @sp.private(with_storage="read-write")
        def _helper(self, x):
            self.data.x = x

    class ViewWithBadStatedEffect(C):
        @sp.onchain_view
        def vw(self):
            # cannot call read-write inherited func from view
            self._helper(2)
            return self.data.x + 1


@sp.add_test()
def test_view_effects04():
    try:
        _ = sp.test_scenario("TestViewEffects04", view_effects04)
    except sp.TypeError_ as e:
        print(e)
    else:
        assert False


@sp.module
def view_effects05():
    class ViewWithBadStatedEffect(sp.Contract):
        def __init__(self, x: sp.nat):
            self.data.x = x

        @sp.private(with_storage="read-only")
        def _helper(self, x):
            return x + self.data.x

        @sp.onchain_view(with_storage="no-access")
        def vw(self):
            return self._helper(2)


@sp.add_test()
def test_view_effects05():
    try:
        _ = sp.test_scenario("TestViewEffects05", view_effects05)
    except sp.TypeError_ as e:
        print(e)
    else:
        assert False


@sp.module
def priv_effects_helper():
    def helper(x):
        assert x > 0
        return x + 1


@sp.module
def priv_effects():
    class PrivWithBadStatedEffect(sp.Contract):
        def __init__(self, x):
            self.data.x = x

        @sp.private(with_exceptions=False)
        def _helper2(self, x):
            return priv_effects_helper.helper(x)


@sp.add_test()
def test_priv_effects():
    try:
        _ = sp.test_scenario("TestPrivEffects", [priv_effects_helper, priv_effects])
    except sp.TypeError_ as e:
        print(e)
    else:
        assert False


@sp.module
def dyn_contract_effects():
    class Created(sp.Contract):
        def __init__(self):
            self.data.a = sp.int(0)
            self.data.b = sp.nat(0)

        @sp.entrypoint
        def myEntryPoint(self, params):
            self.data.a += params.x
            self.data.b += params.y

    class Creator(sp.Contract):
        def __init__(self):
            self.data.x = None

        @sp.entrypoint(with_operations=False)
        def create1(self):
            self.data.x = sp.Some(
                sp.create_contract(
                    Created,
                    None,
                    sp.mutez(123),
                    sp.record(a=12, b=15),
                )
            )


@sp.add_test()
def test_dyn_contract_effects():
    try:
        _ = sp.test_scenario("TestDynContractEffects", dyn_contract_effects)
    except sp.TypeError_ as e:
        print(e)
    else:
        assert False
