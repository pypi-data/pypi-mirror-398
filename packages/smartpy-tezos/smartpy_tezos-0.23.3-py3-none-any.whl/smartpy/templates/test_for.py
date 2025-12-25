import smartpy as sp


@sp.module
def main():
    import smartpy.stdlib.utils as utils

    def matrix(vms):
        mm = {}
        km = 0
        for vvs in vms:
            mv = {}
            kv = 0
            for vv in vvs:
                mv[kv] = vv
                kv += 1
            mm[km] = mv
            km += 1
        return mm

    def cube(vcs):
        mc = {}
        kc = 0
        for vms in vcs:
            mm = {}
            km = 0
            for vvs in vms:
                mv = {}
                kv = 0
                for vv in vvs:
                    mv[kv] = vv
                    kv += 1
                mm[kv] = mv
                km += 1
            mc[kc] = mm
        return mc

    class C(sp.Contract):
        def __init__(self):
            self.data.x = 0
            self.data.xxs = matrix([[0]])
            self.data.xxxs = cube([[[0]]])
            self.data.rs = [sp.record(a=5, b=6)]
            self.data.ms = [{"a": 97, "b": 98}, {"a": 0, "b": 1}]

        @sp.entrypoint
        def ep1(self):
            self.data.x = 0
            r = sp.record(a=2, b=3)
            s = sp.record(a=5, b=6)
            for i in [r, s]:
                self.data.x += i.a  # read record attribute
            assert self.data.x == 7

        @sp.entrypoint
        def ep2(self):
            self.data.x = 2
            for i in [self.data.x, self.data.x, self.data.x]:
                self.data.x += i  # write to something mentioned in the list (no effect)
            assert self.data.x == 8

        @sp.entrypoint
        def ep3(self):
            r = sp.record(a=2, b=3)
            self.data.rs = [r, r, r]
            for i in self.data.rs:
                i.a = 0  # write to record attribute
            # r = sp.record(a=0,b=3)
            # sp.verify(self.data.rs == [r,r,r])

        @sp.entrypoint
        def ep4(self):
            xs = [2, 3]
            self.data.xxs = matrix([xs, xs, xs])
            for xs_ in self.data.xxs.values():
                xs_[0] = 0  # write to sub-list
                sp.send(
                    sp.address("tz1PiDHTNJXhqpkbRUYNZEzmePNd21WcB8yB"),
                    utils.nat_to_mutez(xs_[1]),
                )
            xs = [0, 3]
            # sp.verify(self.data.xxs == [xs,xs,xs])

        @sp.entrypoint
        def ep5(self):
            self.data.x = 0
            self.data.xxxs = cube([[[1]], [[2]]])
            for xs in self.data.xxxs[self.data.x].values():
                self.data.x = 1
                xs[0] = 0
            # sp.verify(self.data.xxxs == [[[0]],[[2]]])

        @sp.entrypoint
        def ep6(self):
            self.data.xxxs = cube([[[0], [10]], [[20], [30]]])
            for xs in self.data.xxxs[self.data.xxxs[0][0][0]].values():
                xs[0] = 1
            # sp.verify(self.data.xxxs == [[[1],[1]],[[20],[30]]])

        @sp.entrypoint
        def ep7(self):
            self.data.ms = [{"a": 97, "b": 98}, {"a": 0, "b": 1}]
            for m in self.data.ms:
                del m["a"]
            # assert self.data.ms == [{'b': 98}, {'b': 1}]


@sp.add_test()
def test():
    s = sp.test_scenario("For")
    c = main.C()
    s += c
    c.ep1()
    c.ep2()
    c.ep3()
    # c.ep4()
    # c.ep5()
    # c.ep6()
    c.ep7()
