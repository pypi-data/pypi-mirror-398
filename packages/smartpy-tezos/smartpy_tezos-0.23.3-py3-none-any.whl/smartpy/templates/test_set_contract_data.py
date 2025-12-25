import smartpy as sp


@sp.module
def main():
    class MyContract(sp.Contract):
        def __init__(self):
            self.data.x = 0
            self.data.y = sp.record(a=1, b="test")
            self.data.z = sp.cast(None, sp.option[sp.nat])

        @sp.entrypoint
        def set_x(self, x):
            self.data.x = x


if "templates" not in __name__:

    @sp.add_test()
    def test():
        sc = sp.test_scenario("MyContract")
        c1 = main.MyContract()
        c1.data.x = 5
        c1.data.x = 6
        c1.data.y = sp.record(a=2, b="test2")
        # c1.data = sp.record(x=c1.data.x, y=c1.data.y, z=sp.Some(1))

        def assert_set_x_fails(field, value, detail):
            try:
                setattr(c1.data, field, value)
            except:
                pass
            else:
                # Don't raise error if the scenario failed earlier.
                # Needed for mockup.
                if sc.failed:
                    return
                raise AssertionError(
                    f"`c1.data.{field} = {value}` should fail {detail}"
                )

        assert_set_x_fails("x", "", "due to type inconsistency: sp.string to a sp.int")
        assert_set_x_fails("a", 0, "because field 'a' doesn't exist")
        sc += c1
        assert_set_x_fails("x", 0, "after origination")

        sc.verify(c1.data.x == 6)
        sc.verify(c1.data.y.a == 2)
        # sc.verify(c1.data.z == sp.Some(1))
        c1.set_x(42)

        c2 = main.MyContract()
        c2.data.x = c1.data.x
        sc += c2
        if sc.simulation_mode() is sp.SimulationMode.MOCKUP:
            sc.p("mockups - TODO fix nested calls")
        else:
            sc.verify(c2.data.x == c1.data.x)
