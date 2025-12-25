import smartpy as sp


@sp.module
def main():
    class AdminHandOver(sp.Contract):
        """This is an example contract that implements a mechanism to switch
        administrator (an address that with special permission) in a way that
        prevents the administrator from handing over to an address with a typo
        or a contract without an interaction code.

        The problem: An administrator hands the contract over to a new
        administrator and then discovers that they made a typing error in the
        address. In this case, the contract can no longer be administered.

        The solution: The administrator hand over is a two step process:
        1. the current administrator adds a candidate admin.
        2. the new administrator removes the old one.
        """

        def __init__(self, admins: sp.set[sp.address]):
            """
            Args:
                admins (sp.set of sp.address): The contract's administrators.
            """
            self.data.admins = admins

        @sp.entrypoint
        def add_admins(self, admins):
            """Add new administrators.

            Args:
                admins (sp.list of sp.address): The new admins.
            Raises:
                `Only an admin can call this entrypoint.`
            """
            assert self.data.admins.contains(
                sp.sender
            ), "Only an admin can call this entrypoint."

            for admin in admins:
                self.data.admins.add(admin)

        @sp.entrypoint
        def remove_admins(self, admins):
            """Remove administrators.

            An admin cannot remove themselves.

            Args:
                admins (sp.list of sp.address): The admins to remove.
            Raises:
                `Only an admin can call this entrypoint.`
                `An admin cannot remove themselves.`
            """
            assert self.data.admins.contains(
                sp.sender
            ), "Only an admin can call this entrypoint."

            for admin in admins:
                assert admin != sp.sender, "An admin cannot remove themselves."
                self.data.admins.remove(admin)

        @sp.entrypoint
        def protected(self):
            """Example of entrypoint reserved to administrators.

            Raises:
                `Only an admin can call this entrypoint.`
            """
            assert self.data.admins.contains(
                sp.sender
            ), "Only an admin can call this entrypoint."


# This prevent tests from being executed on importation.
if "main" in __name__:
    first_admin = sp.test_account("first_admin")
    new_admin = sp.test_account("new_admin")
    non_admin = sp.test_account("non_admin")

    @sp.add_test()
    def basic_scenario():
        """Test:
        - Origination
        - An admin adds a new admin.
        - The new admin removes the older admin.
        - The new admin calls the protected entrypoint.
        """
        sc = sp.test_scenario("Admin hand over basic scenario")
        sc.h1("Basic scenario.")

        sc.h2("Origination.")
        c1 = main.AdminHandOver(admins={first_admin.address})
        sc += c1

        sc.h2("An admin adds a new admin.")
        c1.add_admins([new_admin.address], _sender=first_admin)

        sc.h2("The new admin removes the older admin.")
        c1.remove_admins([first_admin.address], _sender=new_admin)

        sc.h2("The new admin calls the protected entrypoint")
        c1.protected(_sender=new_admin)

    @sp.add_test()
    def test():
        sc = sp.test_scenario("Full")
        sc.h1("Full test")
        sc.h2("Origination")
        c1 = main.AdminHandOver(admins={first_admin.address})
        sc += c1

        sc.h2("add_admins")
        sc.h3("(Failure) Non admin fails to a new admin.")
        c1.add_admins(
            [new_admin.address],
            _sender=non_admin,
            _valid=False,
            _exception="Only an admin can call this entrypoint.",
        )
        sc.h3("An admin adds a new admin.")
        c1.add_admins([new_admin.address], _sender=first_admin)

        sc.h2("remove_admins")
        sc.h3("(Failure) Non admin fails to remove the older admin.")
        c1.remove_admins(
            [first_admin.address],
            _sender=non_admin,
            _valid=False,
            _exception="Only an admin can call this entrypoint.",
        )
        sc.h3("(Failure) Admin tries to remove themselves.")
        c1.remove_admins(
            [first_admin.address],
            _sender=first_admin,
            _valid=False,
            _exception="An admin cannot remove themselves.",
        )
        sc.h3("The new admin removes the older admin.")
        c1.remove_admins([first_admin.address], _sender=new_admin)
        sc.verify(~c1.data.admins.contains(first_admin.address))

        sc.h2("protected")
        sc.h3("The new admin calls the protected entrypoint")
        c1.protected(_sender=new_admin)
        sc.h3("(Failure) Non admin calls the protected entrypoint")
        c1.protected(
            _sender=non_admin,
            _valid=False,
            _exception="Only an admin can call this entrypoint.",
        )

    # @sp.add_test(name="Mutation")
    # def test():
    #     s = sp.test_scenario()
    #     with s.mutation_test() as mt:
    #         mt.add_scenario("Full")
