import smartpy as sp


@sp.module
def main():
    class BakingSwap(sp.Contract):
        """An example contract that takes tez deposits and pays interest.

        The deposited funds cannot leave the contract, but the administrator can
        delegate them for baking.

        In more detail:

        - The administrator funds the contract with collateral.

        - The administrator publishes an offer: a rate (in basis points) and a
        duration (in days).

        - For each deposit the amount to be paid out and the due date are recorded.
        The corresponding amount of collateral is locked up.

        - At maturity the deposit plus interest can be withdrawn.
        """

        def __init__(self, admin, initialRate, initialDuration):
            """Constructor

            Args:
                admin (sp.address): admin of the contract.
                initialRate (sp.nat): Basis points to compute the interest.
                initialDuration (sp.nat): Number of days before a deposit can be
                    withdrawn.
            """
            self.data.admin = admin
            self.data.collateral = sp.mutez(0)
            self.data.ledger = {}
            self.data.rate = initialRate
            self.data.duration = initialDuration

        # Admin-only entrypoints

        @sp.entrypoint
        def delegate(self, public_key_hash):
            """Admin-only. Delegate the contract's balance to the admin.

            Args:
                public_key_hash (sp.key_hash): public key hash of the admin.
            """
            assert sp.sender == self.data.admin
            assert sp.amount == sp.mutez(0)
            assert sp.sender == sp.to_address(sp.implicit_account(public_key_hash))
            sp.set_delegate(sp.Some(public_key_hash))

        @sp.entrypoint
        def collateralize(self):
            """Admin-only. Provide tez as collateral for interest to be paid."""
            assert sp.sender == self.data.admin
            self.data.collateral += sp.amount

        @sp.entrypoint
        def uncollateralize(self, amount, receiver):
            """Admin-only. Withdraw collateral.

            Transfer `amount` mutez to admin if it doesn't exceed collateral.

            Args:

                amount (sp.mutez): Amount to be removed from the collateral.
            """
            assert sp.sender == self.data.admin
            # Explicitly fails for insufficient collateral.
            assert amount <= self.data.collateral, "insufficient collateral"
            self.data.collateral -= amount
            sp.send(receiver, amount)

        @sp.entrypoint
        def set_offer(self, rate, duration):
            """Admin-only. Set the current offer: interest rate (in basis points)
            and duration.

            Args:
                rate (sp.nat): Basis points to compute the interest.
                duration (sp.nat): Number of days before a deposit can be withdrawn.
            """
            assert sp.sender == self.data.admin
            assert sp.amount == sp.mutez(0)
            self.data.rate = rate
            self.data.duration = duration

        # Permissionless entrypoints

        @sp.entrypoint
        def deposit(self, rate, duration):
            """Deposit tez. The current offer has to be repeated in the parameters.

            Args:
                rate (sp.nat): Basis points to compute the interest.
                duration (sp.nat): Number of days before a deposit can be withdrawn.
            """
            assert self.data.rate >= rate
            assert self.data.duration <= duration
            assert not self.data.ledger.contains(sp.sender)

            # Compute interest to be paid.
            interest = sp.split_tokens(sp.amount, self.data.rate, 10_000)
            self.data.collateral -= interest

            # Record the payment to be made.
            self.data.ledger[sp.sender] = sp.record(
                amount=sp.amount + interest,
                due=sp.add_days(sp.now, self.data.duration),
            )

        @sp.entrypoint
        def withdraw(self, receiver):
            """Withdraw tez at maturity."""
            assert sp.amount == sp.mutez(0)
            entry = self.data.ledger.get(sp.sender, error="NoDeposit")
            assert sp.now >= entry.due
            sp.send(receiver, entry.amount)
            del self.data.ledger[sp.sender]


@sp.module
def testing():
    class Receiver(sp.Contract):
        @sp.entrypoint
        def default(self):
            pass


if "main" in __name__:
    admin = sp.test_account("Admin")
    non_admin = sp.test_account("non_admin")
    voting_powers = {
        admin.public_key_hash: 0,
    }

    @sp.add_test()
    def basic_scenario():
        scenario = sp.test_scenario("Baking swap basic scenario")
        scenario.h1("Baking Swap")
        c = main.BakingSwap(admin.address, 700, 365)
        scenario += c

        if scenario.simulation_mode() is sp.SimulationMode.MOCKUP:
            scenario.p("set delegate doesnt work in mockups")
            return

        c.delegate(admin.public_key_hash, _sender=admin, _voting_powers=voting_powers)

    @sp.add_test()
    def test():
        sc = sp.test_scenario("Full")
        sc.h1("Full test")
        sc.h2("Origination")
        c = main.BakingSwap(admin.address, 0, 10000)
        sc += c
        sc.h2("Delegator")
        delegator = testing.Receiver()
        sc += delegator
        sc.h2("Admin receiver")
        admin_receiver = testing.Receiver()
        sc += admin_receiver

        if sc.simulation_mode() is sp.SimulationMode.MOCKUP:
            sc.p("set delegate doesnt work in mockups")
            return

        sc.h2("delegate")
        c.delegate(admin.public_key_hash, _sender=admin, _voting_powers=voting_powers)
        sc.verify(c.baker == sp.Some(admin.public_key_hash))
        sc.h3("Failures")
        c.delegate(
            admin.public_key_hash,
            _sender=non_admin,
            _voting_powers=voting_powers,
            _valid=False,
            _exception="Assert failure: sp.sender == self.data.admin",
        )
        c.delegate(
            admin.public_key_hash,
            _sender=admin,
            _amount=sp.mutez(1),
            _voting_powers=voting_powers,
            _valid=False,
            _exception="Assert failure: sp.amount == sp.tez(0)",
        )
        c.delegate(
            non_admin.public_key_hash,
            _sender=admin,
            _voting_powers=voting_powers,
            _valid=False,
            _exception="Assert failure: sp.sender == sp.to_address(sp.implicit_account(params))",
        )

        sc.h2("collateralize")
        c.collateralize(_sender=admin, _amount=sp.tez(500))
        sc.verify(c.data.collateral == sp.tez(500))
        sc.h3("Failures")
        c.collateralize(
            _sender=non_admin,
            _amount=sp.tez(500),
            _valid=False,
            _exception="Assert failure: sp.sender == self.data.admin",
        )

        sc.h2("set_offer")
        c.set_offer(rate=1000, duration=365, _sender=admin)
        sc.h3("Failures")
        c.set_offer(
            rate=1000,
            duration=365,
            _sender=non_admin,
            _valid=False,
            _exception="Assert failure: sp.sender == self.data.admin",
        )
        c.set_offer(
            rate=1000,
            duration=365,
            _sender=admin,
            _amount=sp.mutez(1),
            _valid=False,
            _exception="Assert failure: sp.amount == sp.tez(0)",
        )

        sc.h2("deposit")
        c.deposit(
            rate=1000, duration=365, _sender=delegator.address, _amount=sp.tez(100)
        )
        sc.verify(c.data.collateral == sp.tez(490))
        sc.verify(
            c.data.ledger[delegator.address]
            == sp.record(amount=sp.tez(110), due=sp.timestamp(365 * 24 * 3600))
        )
        sc.h3("Failures")
        c.deposit(
            rate=1001,
            duration=365,
            _sender=delegator.address,
            _amount=sp.tez(100),
            _valid=False,
            _exception="Assert failure: self.data.rate >= params.rate",
        )
        c.deposit(
            rate=1000,
            duration=364,
            _sender=delegator.address,
            _amount=sp.tez(100),
            _valid=False,
            _exception="Assert failure: self.data.duration <= params.duration",
        )
        c.deposit(
            rate=1000,
            duration=365,
            _sender=delegator.address,
            _amount=sp.tez(100),
            _valid=False,
            _exception="Assert failure: not (self.data.ledger.contains(sp.sender))",
        )

        sc.h2("uncollateralize")
        sc.h3("Failures")
        c.uncollateralize(
            amount=sp.tez(500),
            receiver=admin_receiver.address,
            _sender=admin,
            _valid=False,
            _exception="insufficient collateral",
        )
        c.uncollateralize(
            amount=sp.tez(490),
            receiver=admin_receiver.address,
            _sender=non_admin,
            _valid=False,
            _exception="Assert failure: sp.sender == self.data.admin",
        )
        sc.h3("Valid")
        c.uncollateralize(
            amount=sp.tez(490), receiver=admin_receiver.address, _sender=admin
        )
        sc.verify(c.data.collateral == sp.tez(0))
        sc.verify(admin_receiver.balance == sp.tez(490))

        sc.h2("withdraw")
        sc.h3("Failures")
        c.withdraw(
            delegator.address,
            _sender=delegator.address,
            _amount=sp.mutez(1),
            _now=sp.timestamp(365 * 24 * 3600),
            _valid=False,
            _exception="Assert failure: sp.amount == sp.tez(0)",
        )
        c.withdraw(
            delegator.address,
            _sender=delegator.address,
            _now=sp.timestamp(365 * 24 * 3600 - 1),
            _valid=False,
            _exception="Assert failure: sp.now >= entry.due",
        )
        sc.h3("Valid")
        c.withdraw(
            delegator.address,
            _sender=delegator.address,
            _now=sp.timestamp(365 * 24 * 3600),
        )
        sc.verify(delegator.balance == sp.tez(110))
        sc.verify(~c.data.ledger.contains(delegator.address))
        sc.h3("Failures")
        c.withdraw(
            delegator.address,
            _sender=delegator.address,
            _valid=False,
            _now=sp.timestamp(365 * 24 * 3600),
            _exception="NoDeposit",
        )

    # @sp.add_test(name="Mutation")
    # def test():
    #     s = sp.test_scenario()
    #     with s.mutation_test() as mt:
    #         mt.add_scenario("Full")
