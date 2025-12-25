# Mini-kitties - Example for illustrative purposes only.

# This small example is loosely inspired by CryptoKitties.

import smartpy as sp


@sp.module
def main():
    class MiniKitties(sp.Contract):
        def __init__(self, creator, newAuctionDuration, hatchingDuration):
            self.private.newAuctionDuration = newAuctionDuration
            self.private.hatchingDuration = hatchingDuration
            self.data.kitties = {}
            self.data.creator = creator

        @sp.entrypoint
        def build(self, params):
            assert self.data.creator == sp.sender
            assert params.kitty.isNew
            sp.cast(params.kitty.kittyId, sp.int)
            self.data.kitties[params.kitty.kittyId] = params.kitty

        @sp.entrypoint
        def sell(self, price, params):
            assert sp.mutez(0) <= price
            self.checkAvailable(
                sp.record(
                    kitty=self.data.kitties[params.kittyId],
                    borrowPrice=params.borrowPrice,
                    borrow=False,
                )
            )
            self.data.kitties[params.kittyId].price = params.price

        @sp.entrypoint
        def lend(self, price, params):
            assert sp.mutez(0) <= price
            self.checkAvailable(
                sp.record(
                    kitty=self.data.kitties[params.kittyId],
                    borrowPrice=params.borrowPrice,
                    borrow=False,
                )
            )
            self.data.kitties[params.kittyId].borrowPrice = params.price

        @sp.entrypoint
        def buy(self, params):
            kitty = self.data.kitties[params.kittyId]
            assert sp.mutez(0) < kitty.price
            assert kitty.price <= params.price
            assert sp.amount == params.price
            sp.send(kitty.owner, params.price)
            kitty.owner = sp.sender
            if kitty.isNew:
                kitty.isNew = False
                kitty.auction = sp.add_seconds(sp.now, self.private.newAuctionDuration)
            assert sp.now <= kitty.auction
            if sp.now <= kitty.auction:
                kitty.price = params.price + sp.mutez(1)
            self.data.kitties[params.kittyId] = kitty

        @sp.private(with_storage="read-write", with_operations=True)
        def checkAvailable(self, params):
            if params.borrow:
                assert sp.mutez(0) < params.kitty.borrowPrice
                borrowPrice = params.borrowPrice
                assert params.kitty.borrowPrice < borrowPrice
                assert sp.amount == borrowPrice
                sp.send(params.kitty.owner, borrowPrice)
            assert params.kitty.auction < sp.now
            assert params.kitty.hatching < sp.now

        @sp.private()
        def newKitty(self, params):
            return sp.record(
                kittyId=params.kittyId,
                owner=sp.sender,
                price=sp.mutez(0),
                isNew=False,
                auction=sp.timestamp(0),
                hatching=params.hatching,
                generation=params.generation,
                borrowPrice=sp.mutez(0),
            )

        @sp.entrypoint
        def breed(self, params):
            parent1 = params.parent1
            parent2 = params.parent2
            kitty1 = self.data.kitties[parent1]
            kitty2 = self.data.kitties[parent2]
            assert parent1 != parent2
            self.checkAvailable(
                sp.record(kitty=kitty1, borrowPrice=params.borrowPrice, borrow=False)
            )
            self.checkAvailable(
                sp.record(
                    kitty=kitty2,
                    borrowPrice=params.borrowPrice,
                    borrow=kitty2.owner != sp.sender,
                )
            )
            hatching = sp.add_seconds(sp.now, self.private.hatchingDuration)
            self.data.kitties[parent1].hatching = hatching
            self.data.kitties[parent2].hatching = hatching
            kitty = self.newKitty(
                sp.record(
                    kittyId=params.kittyId,
                    hatching=hatching,
                    generation=1 + sp.max(kitty1.generation, kitty2.generation),
                )
            )
            self.data.kitties[kitty.kittyId] = kitty


@sp.add_test()
def test():
    creator = sp.test_account("Creator")
    alice = sp.test_account("Alice")
    bob = sp.test_account("Robert")

    scenario = sp.test_scenario("MiniKitties")
    c1 = main.MiniKitties(
        creator=creator.address, newAuctionDuration=10, hatchingDuration=100
    )
    scenario.h1("Mini Kitties")
    scenario += c1

    if scenario.simulation_mode() is sp.SimulationMode.MOCKUP:
        scenario.p("timestamp doesnt work in mockups")
        return

    def newKitty(kittyId, price):
        return sp.record(
            kittyId=kittyId,
            owner=creator.address,
            price=sp.mutez(price),
            isNew=True,
            auction=sp.timestamp(0),
            hatching=sp.timestamp(0),
            generation=0,
            borrowPrice=sp.mutez(0),
        )

    c1.build(kitty=newKitty(0, 10), _sender=creator)
    c1.build(kitty=newKitty(1, 10), _sender=creator)
    c1.build(kitty=newKitty(2, 10), _sender=creator)
    c1.build(kitty=newKitty(3, 10), _sender=creator)
    c1.buy(kittyId=1, price=sp.mutez(10), _sender=alice, _amount=sp.mutez(10))
    c1.buy(kittyId=2, price=sp.mutez(10), _sender=alice, _amount=sp.mutez(10))
    c1.buy(
        kittyId=1,
        price=sp.mutez(11),
        _sender=bob,
        _amount=sp.mutez(11),
        _now=sp.timestamp(3),
    )
    c1.buy(
        kittyId=1,
        price=sp.mutez(15),
        _sender=alice,
        _amount=sp.mutez(15),
        _now=sp.timestamp(9),
    )
    scenario.h2("A bad execution")
    c1.buy(
        kittyId=1,
        price=sp.mutez(20),
        _sender=bob,
        _amount=sp.mutez(20),
        _now=sp.timestamp(13),
        _valid=False,
    )
    scenario.h2("Hatching")
    c1.breed(
        borrowPrice=sp.mutez(10),
        kittyId=4,
        parent1=1,
        parent2=2,
        _sender=alice,
        _now=sp.timestamp(15),
    )
