import smartpy as sp


@sp.module
def pass_module():
    pass


@sp.module
def main():
    """this is a module"""

    def m():
        """a module function"""
        return 2

    class C(sp.Contract):
        """this is a class"""

        def __init__(self):
            """the init method"""
            self.data.result = 0

        @sp.entrypoint
        def ep(self):
            """an entrypoint"""
            self.data.result += 1

        @sp.onchain_view
        def vw(self):
            """a view"""
            return self.data.result

        @sp.private
        def f(self):
            """a private method"""
            return 1


@sp.add_test()
def test():
    scenario = sp.test_scenario("annots")
    scenario += main.C()
