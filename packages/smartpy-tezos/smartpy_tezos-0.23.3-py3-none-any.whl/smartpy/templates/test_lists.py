# Lists - Example for illustrative purposes only.

import smartpy as sp


@sp.module
def main():
    class TestLists(sp.Contract):
        def __init__(self):
            self.data.a = None
            self.data.b = 0
            self.data.c = ""
            self.data.d = 0
            self.data.e = ""
            self.data.f = []
            self.data.g = []
            self.data.head = "no head"
            self.data.tail = ["no tail"]
            self.data.total = 0
            self.data.xs2 = []

        @sp.entrypoint
        def test(self, params):
            result = sp.record(
                l=params.l,
                lr=reversed(params.l),
                # from maps
                mi=params.m.items(),
                mir=reversed(params.m.items()),
                mk=params.m.keys(),
                mkr=reversed(params.m.keys()),
                mv=params.m.values(),
                mvr=reversed(params.m.values()),
                # from sets
                s=params.s.elements(),
                sr=reversed(params.s.elements()),
            )
            self.data.a = sp.Some(result)
            self.data.b = sum(result.l)
            self.data.c = sp.concat(result.mk)  # string list concatenation
            self.data.d = sum(result.sr)  # int    list sum
            self.data.e = ""

            # iterations
            for x in result.mv:
                if sp.snd(x):
                    self.data.e += sp.fst(x)

            # ranges
            for i in range(0, 5):
                self.data.f.push(i * i)

            self.data.g = range(1, 12)

        @sp.private(with_storage="read-write", with_operations=True)
        def f(self, param) -> sp.nat:
            (x, to_) = param
            self.data.total += x
            sp.send(to_, sp.mul(sp.tez(1), x))
            return 2 * x

        @sp.entrypoint
        def test_comprehensions(self, to_):
            xs = [1, 2, 3]
            c = 1
            assert sp.pack([x + c for x in xs]) == sp.pack([2, 3, 4])
            c = 2
            assert sp.pack([x + c for x in xs]) == sp.pack([3, 4, 5])
            self.data.xs2 = [self.f((n, to_)) for n in xs]

        # @sp.entrypoint
        # def test_match(self, params):
        #     with sp.match_cons(params) as x1:
        #         self.data.head = x1.head
        #         self.data.tail = x1.tail
        #     else:
        #         self.data.head = "abc"

        # @sp.entrypoint
        # def test_match2(self, params):
        #     with sp.match_cons(params) as x1:
        #         with sp.match_cons(x1.tail) as x2:
        #             self.data.head = x1.head + x2.head
        #             self.data.tail = x2.tail
        #     sp.else:
        #         self.data.head = "abc"

    class R(sp.Contract):
        @sp.entrypoint
        def default(self):
            pass


@sp.add_test()
def test():
    scenario = sp.test_scenario("Lists")
    r = main.R()
    scenario.h1("Helper contract")
    scenario += r

    c1 = main.TestLists()
    scenario.h1("Lists")
    scenario += c1

    c1.test(
        l=[1, 2, 3],
        m={"a": ("aa", True), "b": ("bb", False), "c": ("cc", True)},
        s={1, 12, 100},
    )

    # c1.test_match(['1', '2', '3'])

    # TODO: active this one when test_match is activated
    # target = sp.record(a = sp.Some(
    #     sp.record(l   = sp.list([1, 2, 3]),
    #               lr  = sp.list([3, 2, 1]),
    #               mi  =  sp.list([sp.record(key = 'a', value = ('aa', True)),
    #                               sp.record(key = 'b', value = ('bb', False)),
    #                               sp.record(key = 'c', value = ('cc', True))]),
    #               mir = sp.list([sp.record(key = 'c', value = ('cc', True)),
    #                              sp.record(key = 'b', value = ('bb', False)),
    #                              sp.record(key = 'a', value = ('aa', True))]),
    #               mk  = sp.list(['a', 'b', 'c']),
    #               mkr = sp.list(['c', 'b', 'a']),
    #               mv  = sp.list([('aa', True), ('bb', False), ('cc', True)]),
    #               mvr = sp.list([('cc', True), ('bb', False), ('aa', True)]),
    #               s   = sp.list([1, 12, 100]),
    #               sr  = sp.list([100, 12, 1]))),
    #                    b = 6,
    #                    c = 'abc',
    #                    d = 113,
    #                    e = 'aacc',
    #                    f = [16, 9, 4, 1, 0],
    #                    g = range(1, 12),
    #                    head = "1",
    #                    tail = ["2", "3"],
    #                    )
    target = sp.record(
        a=sp.Some(
            sp.record(
                l=sp.list([1, 2, 3]),
                lr=sp.list([3, 2, 1]),
                mi=sp.list(
                    [
                        sp.record(key="a", value=("aa", True)),
                        sp.record(key="b", value=("bb", False)),
                        sp.record(key="c", value=("cc", True)),
                    ]
                ),
                mir=sp.list(
                    [
                        sp.record(key="c", value=("cc", True)),
                        sp.record(key="b", value=("bb", False)),
                        sp.record(key="a", value=("aa", True)),
                    ]
                ),
                mk=sp.list(["a", "b", "c"]),
                mkr=sp.list(["c", "b", "a"]),
                mv=sp.list([("aa", True), ("bb", False), ("cc", True)]),
                mvr=sp.list([("cc", True), ("bb", False), ("aa", True)]),
                s=sp.list([1, 12, 100]),
                sr=sp.list([100, 12, 1]),
            )
        ),
        b=6,
        c="abc",
        d=113,
        e="aacc",
        f=[16, 9, 4, 1, 0],
        g=range(1, 12),
        head="no head",
        tail=["no tail"],
        total=0,
        xs2=[],
    )

    scenario.verify_equal(c1.data, target)

    # c1.test_match2(['1', '2', '3'])

    # scenario.verify_equal(c1.data.tail, ['3'])
    # scenario.verify_equal(c1.data.head, '12')

    c1.test_comprehensions(r.address, _amount=sp.tez(6))
    scenario.verify_equal(c1.data.xs2, [2, 4, 6])
    scenario.verify(c1.data.total == 6)
    scenario.verify(r.balance == sp.tez(6))
