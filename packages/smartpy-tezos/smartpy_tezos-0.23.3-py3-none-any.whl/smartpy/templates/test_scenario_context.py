import smartpy as sp


@sp.module
def main():
    class Contract(sp.Contract):
        @sp.entrypoint
        def a(self):
            pass


# Contract cannot be instantiated before the test scenario is created.
try:
    main.Contract()
except Exception as e:
    print(e)
else:
    assert False

sc = sp.test_scenario("A")

# Contract can be instantiated after the test scenario is created.
# c is linked to sc and cannot be added to a different test scenario.
c = main.Contract()

sc2 = sp.test_scenario("B")

# Same contract class can be instantiated in different test scenarios.
sc2 += main.Contract()

# c is linked to sc and cannot be added to sc2.
try:
    sc2 += c
except Exception as e:
    print(e)
else:
    assert False

# c can be added to sc even after sc2 is created.
sc += c

# Contract cannot be added to the same test scenario twice.
try:
    sc += c
except Exception as e:
    print(e)
else:
    assert False
