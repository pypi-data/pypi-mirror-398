import smartpy as sp


@sp.module
def main():
    class MyContract(sp.Contract):
        def __init__(self):
            self.data.x = "<img src=x onerror=alert(document.domain)>"

        @sp.private(with_storage="read-write")
        def p(self):
            self.data.x = "<img src=x onerror=alert(document.domain)>"

        @sp.entrypoint
        def ep(self):
            self.data.x = "<img src=x onerror=alert(document.domain)>"

        @sp.entrypoint
        def ep2(self):
            self.p()

        @sp.entrypoint
        def ep3(self, x):
            self.data.x = x

        @sp.onchain_view()
        def ov(self):
            return self.data.x


if "main" in __name__:

    @sp.add_test()
    def test():
        sc = sp.test_scenario("Test")
        c1 = main.MyContract()
        sc += c1
        c1.ep()
        c1.ep2()
        c1.ep3("<img src=x onerror=alert(document.domain)>")
        sc.show(c1.ov())
        sc.show("<img src=x onerror=alert(document.domain)>")
