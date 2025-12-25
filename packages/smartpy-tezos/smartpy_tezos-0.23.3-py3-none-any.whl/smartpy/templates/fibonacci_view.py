import smartpy as sp


@sp.module
def main():
    class FibonacciView(sp.Contract):
        """Contract with a recursing view to compute the sum of fibonacci numbers."""

        @sp.onchain_view()
        def fibonacci(self, n: sp.int):
            """Return the sum of fibonacci numbers until n.

            Args:
                n (sp.int): number of fibonacci numbers to sum.
            Return:
                (sp.int): the sum of fibonacci numbers
            """
            if n < 2:
                return n
            else:
                n1 = sp.view("fibonacci", sp.self_address, n - 1, int).unwrap_some()
                n2 = sp.view("fibonacci", sp.self_address, n - 2, int).unwrap_some()
                return n1 + n2


if "main" in __name__:

    @sp.add_test()
    def basic_scenario():
        sc = sp.test_scenario("FibonacciView basic scenario")
        sc.h1("Basic scenario.")
        sc.h2("Origination.")
        c1 = main.FibonacciView()
        sc += c1
        sc.verify(c1.fibonacci(8) == 21)
