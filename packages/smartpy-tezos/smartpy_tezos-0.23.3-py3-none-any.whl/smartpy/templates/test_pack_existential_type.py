"""
Test for issue #225: pack of existential raises assert false

This test verifies that packing an existential type generates an error
in the compilation file instead of crashing the compiler.
"""

import smartpy as sp


@sp.module
def main():
    class C(sp.Contract):
        def __init__(self):
            pass

        @sp.entrypoint
        def ep(self, x):
            # This generates an error in the compilation file
            _ = sp.pack(x)


sc = sp.test_scenario("Test", main)
c1 = main.C()
sc += c1
