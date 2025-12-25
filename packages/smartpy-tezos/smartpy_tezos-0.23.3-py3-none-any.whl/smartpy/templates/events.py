import smartpy as sp


@sp.module
def main():
    class C(sp.Contract):
        @sp.entrypoint
        def ep(self):
            sp.emit("Hello")
            sp.emit("World", tag="mytag")
            sp.emit(sp.record(a="ABC", b="XYZ"), tag="mytag2")
            sp.emit(sp.record(a="ABC", b="XYZ"), tag="mytag2", with_type=False)


@sp.add_test()
def test():
    s = sp.test_scenario("Events")
    c = main.C()
    s += c
    c.ep()
