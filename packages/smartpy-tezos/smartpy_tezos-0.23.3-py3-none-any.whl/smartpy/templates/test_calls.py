import smartpy as sp


@sp.module
def main():
    class Default1(sp.Contract):
        def __init__(self):
            self.data.x = sp.tez(0)

        @sp.entrypoint
        def default(self):
            self.data.x = sp.amount

    class Default2(sp.Contract):
        def __init__(self):
            self.data.x = sp.tez(0)

        @sp.entrypoint
        def default(self):
            self.data.x = sp.amount

        @sp.entrypoint
        def other(self):
            pass

    class Regular_annotation1(sp.Contract):
        def __init__(self):
            self.data.x = sp.tez(0)

        @sp.entrypoint
        def reg_annot(self):
            self.data.x = sp.amount

    class Regular_annotation2(sp.Contract):
        def __init__(self):
            self.data.x = sp.tez(0)

        @sp.entrypoint
        def reg_annot(self):
            self.data.x = sp.amount

        @sp.entrypoint
        def other(self):
            pass

    class No_annotation(sp.Contract):
        def __init__(self):
            self.data.x = sp.tez(0)

        @sp.entrypoint
        def no_annot(self):
            self.data.x = sp.amount

    class Test(sp.Contract):
        @sp.entrypoint
        def send(self, address, amount):
            sp.send(address, amount)


@sp.add_test()
def test():
    scenario = sp.test_scenario("Test")
    target_default1 = main.Default1()
    target_default2 = main.Default2()
    target_regular1 = main.Regular_annotation1()
    target_regular2 = main.Regular_annotation2()
    target_no_annot = main.No_annotation()

    test = main.Test()
    test.set_initial_balance(sp.tez(1))

    scenario += target_default1
    scenario += target_default2
    scenario += target_regular1
    scenario += target_regular2

    scenario.add_flag("no-single-entrypoint-annotation")
    scenario += target_no_annot

    scenario.add_flag("single-entrypoint-annotation")
    scenario += test

    test.send(address=target_default1.address, amount=sp.mutez(1))
    test.send(address=target_default2.address, amount=sp.mutez(2))
    test.send(address=target_regular1.address, amount=sp.mutez(3))
    test.send(
        address=target_regular2.address,
        amount=sp.mutez(4),
        _valid=False,
        _exception="Not the proper variant constructor [Some] != [None]",
    )
    test.send(address=target_no_annot.address, amount=sp.mutez(5))

    test.send(
        address=sp.to_address(
            sp.contract(sp.unit, target_default1.address).unwrap_some()
        ),
        amount=sp.mutez(6),
    )
    test.send(
        address=sp.to_address(
            sp.contract(sp.unit, target_default2.address).unwrap_some()
        ),
        amount=sp.mutez(7),
    )
    test.send(
        address=sp.to_address(
            sp.contract(
                sp.unit, target_regular1.address, entrypoint="reg_annot"
            ).unwrap_some()
        ),
        amount=sp.mutez(8),
    )
    test.send(
        address=sp.to_address(
            sp.contract(
                sp.unit, target_regular2.address, entrypoint="reg_annot"
            ).unwrap_some()
        ),
        amount=sp.mutez(9),
    )
    # test.send(address=sp.to_address(sp.contract(sp.unit, target_no_annot.address, entrypoint="no_annot").unwrap_some()), amount=sp.mutez(10), _valid = False, exception="No annotation in contract")


@sp.add_test()
def test_option():
    scenario = sp.test_scenario(name="Test_option")
    scenario.add_module(main)

    target_default1 = main.Default1()
    target_default2 = main.Default2()
    target_regular1 = main.Regular_annotation1()
    target_regular2 = main.Regular_annotation2()
    target_no_annot = main.No_annotation()

    test = main.Test()
    test.set_initial_balance(sp.tez(1))

    scenario += target_default1
    scenario += target_default2
    scenario += target_regular1
    scenario += target_regular2

    scenario.add_flag("no-single-entrypoint-annotation")
    scenario += target_no_annot

    scenario.add_flag("single-entrypoint-annotation")
    scenario += test

    test.send(address=target_default1.address, amount=sp.mutez(1))
    test.send(address=target_default2.address, amount=sp.mutez(2))
    test.send(address=target_regular1.address, amount=sp.mutez(3))
    test.send(
        address=target_regular2.address,
        amount=sp.mutez(4),
        _valid=False,
        _exception="Not the proper variant constructor [Some] != [None]",
    )
    test.send(address=target_no_annot.address, amount=sp.mutez(5))

    test.send(
        address=sp.to_address(
            sp.contract(sp.unit, target_default1.address).unwrap_some()
        ),
        amount=sp.mutez(6),
    )
    test.send(
        address=sp.to_address(
            sp.contract(sp.unit, target_default2.address).unwrap_some()
        ),
        amount=sp.mutez(7),
    )
    test.send(
        address=sp.to_address(
            sp.contract(
                sp.unit, target_regular1.address, entrypoint="reg_annot"
            ).unwrap_some()
        ),
        amount=sp.mutez(8),
    )
    test.send(
        address=sp.to_address(
            sp.contract(
                sp.unit, target_regular2.address, entrypoint="reg_annot"
            ).unwrap_some()
        ),
        amount=sp.mutez(9),
    )
    # test.send(address=sp.to_address(sp.contract(sp.unit, target_no_annot.address).unwrap_some()), amount=sp.mutez(10), _valid = False, _exception="Not the proper variant constructor [Some] != [None]")
