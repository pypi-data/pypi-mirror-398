# Calculator - Example for illustrative purposes only.

import smartpy as sp

if "main" in __name__:

    @sp.add_test()
    def test():
        scenario = sp.test_scenario("Calculator")
        main1 = scenario.add_module("smartpy/templates/calculator_main.spy")
        c1 = main1.Calculator()
        scenario.h1("Calculator")
        scenario += c1
        scenario.verify(c1.data.result == 0)
        scenario.verify(c1.data.i == 10)
        # TODO do we want to support this kind of thing?
        try:
            scenario.verify(main1.math.pow((10, 2)) == 100)
        except:
            # error Ref class is not callable
            pass
        c1.multiply(x=2, y=5)
        c1.add(x=2, y=5)
        c1.add(x=2, y=5)
        c1.square(12)
        c1.squareRoot(0)
        c1.squareRoot(1234)
        c1.factorial(100)
        c1.log2(c1.data.result)
        scenario.verify(c1.data.result == 524)
