import smartpy as sp


@sp.module
def M():
    class C(sp.Contract):
        def __init__(self):
            pass

        @sp.private
        def test_head_tail(self):
            lst = [1, 2, 3]
            match lst:
                case []:
                    assert False, "Should not match empty list"
                case [h, *tail]:
                    assert h == 1
                    assert sp.pack(tail) == sp.pack([2, 3])

        @sp.private
        def test_match_empty(self):
            lst = sp.cast([], sp.list[sp.int])
            match lst:
                case []:
                    assert True, "Should match empty list"
                case [h, *tail]:
                    assert False, "Should not match a non-empty list"

        @sp.private
        def test_match_singleton(self):
            lst = [42]
            match lst:
                case []:
                    assert False, "Should not match a non-empty list"
                case [h, *tail]:
                    assert h == 42
                    assert sp.len(tail) == 0

        @sp.entrypoint
        def ep(self):
            self.test_head_tail()
            self.test_match_empty()
            self.test_match_singleton()


@sp.add_test()
def test():
    s = sp.test_scenario("Test")
    c = M.C()
    s += c
    c.ep()
