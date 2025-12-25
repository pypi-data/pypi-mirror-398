import smartpy as sp


@sp.module
def M():
    import smartpy.stdlib.statistics as st

    class C(sp.Contract):
        def __init__(self):
            pass

        @sp.private
        def test_median(self):
            assert st.median([1, 3, 5, 7, 9, 11, 13]) == 7
            assert st.median([3, 13, 2, 34, 11, 26, 47]) == 13
            assert (
                st.median([4, 17, 77, 25, 22, 23, 92, 82, 40, 24, 14, 12, 67, 23, 29])
                == 24
            )

        @sp.entrypoint
        def ep(self):
            self.test_median()


@sp.add_test()
def test():
    s = sp.test_scenario("Test")
    c = M.C()
    s += c
    c.ep()
