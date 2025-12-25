import smartpy as sp


@sp.module
def main():
    class TestUnification(sp.Contract):
        def __init__(self):
            self.data.x = None

        @sp.entrypoint
        def push(self, params):
            sp.cast(params, sp.int)
            self.data.x = sp.Some(params)


if "main" in __name__:

    @sp.add_test()
    def test():
        scenario = sp.test_scenario("TestUnification")
        c1 = main.TestUnification()
        scenario += c1
        c1.push(4)
