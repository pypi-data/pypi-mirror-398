import smartpy as sp

# This is the SmartPy editor.
# You can experiment with SmartPy by loading a template.
# (in the Commands menu above this editor)
#
# A typical SmartPy program has the following form:


# A SmartPy module
@sp.module
def main():
    # A class of contracts
    class MyContract(sp.Contract):
        def __init__(self, my_parameter_1, my_parameter_2):
            self.data.my_parameter_1 = my_parameter_1
            self.data.my_parameter_2 = my_parameter_2

        # An entrypoint, i.e., a message receiver
        # (contracts react to messages)
        @sp.entrypoint
        def my_entrypoint(self, params):
            assert self.data.my_parameter_1 <= 123
            self.data.my_parameter_1 += params


# Tests
@sp.add_test()
def test():
    # We define a test scenario, together with some outputs and checks
    # The scenario takes the module as a parameter
    scenario = sp.test_scenario("Welcome")
    scenario.h1("Welcome")

    # We first define a contract and add it to the scenario
    c1 = main.MyContract(12, 123)
    scenario += c1

    # And call some of its entrypoints
    c1.my_entrypoint(12)
    c1.my_entrypoint(13)
    c1.my_entrypoint(14)
    c1.my_entrypoint(50)
    c1.my_entrypoint(50)
    c1.my_entrypoint(50, _valid=False)  # this is expected to fail
    # Finally, we check its final storage
    scenario.verify(c1.data.my_parameter_1 == 151)

    # We can define another contract using the current state of c1
    c2 = main.MyContract(1, c1.data.my_parameter_1)
    scenario += c2
    scenario.verify(c2.data.my_parameter_2 == 151)
