# Two Level Multisig - Example for illustrative purposes only.

import smartpy as sp

# MultiSigFactory is a two level multisig factory contract
# - two level because to validate a property, we can use several groups of participants and not only one group,
# - and a factory because it can hold several such two level multisig contracts.


@sp.module
def t():
    participant: type = sp.record(hasVoted=sp.bool, weight=sp.int, id=sp.address)

    group: type = sp.record(
        weight=sp.int,
        voters=sp.int,
        contractWeight=sp.int,
        thresholdWeight=sp.int,
        thresholdVoters=sp.int,
        participants=sp.list[participant],
        ok=sp.bool,
    )

    contract: type = sp.record(
        amount=sp.mutez,
        name=sp.string,
        owner=sp.address,
        thresholdGroupsOK=sp.int,
        groupsOK=sp.int,
        thresholdWeight=sp.int,
        weight=sp.int,
        groups=sp.list[group],
        ok=sp.bool,
    )


@sp.module
def main():
    import t

    class MultiSigFactory(sp.Contract):
        def __init__(self):
            self.data.multisigs = sp.cast(sp.big_map(), sp.big_map[sp.nat, t.contract])
            self.data.nbMultisigs = sp.nat(0)

        @sp.entrypoint
        def build(self, params):
            self.data.multisigs[self.data.nbMultisigs] = params.contract
            self.data.nbMultisigs += 1

        @sp.entrypoint
        def sign(self, id, contractId, contractName):
            assert id == sp.sender
            sp.cast(contractName, sp.string)
            contract = self.data.multisigs[contractId]
            assert contractName == contract.name
            sp.cast(contract.weight, sp.int)
            sp.cast(contract.groupsOK, sp.int)
            for group in contract.groups:
                for participant in group.participants:
                    if participant.id == id:
                        assert not participant.hasVoted
                        participant.hasVoted = True
                        sp.cast(group.weight, sp.int)
                        group.weight += participant.weight
                        group.voters += 1
                        if (
                            not group.ok
                            and group.thresholdVoters <= group.voters
                            and group.thresholdWeight <= group.weight
                        ):
                            group.ok = True
                            contract.weight += group.contractWeight
                            contract.groupsOK += 1
                            if (
                                not contract.ok
                                and contract.thresholdGroupsOK <= contract.groupsOK
                                and contract.thresholdWeight <= contract.weight
                            ):
                                contract.ok = True
                                self.onOK(contract)

        @sp.private(with_storage="read-write", with_operations=True)
        def onOK(self, contract):
            return ()

    # MultiSigFactoryWithPayment inherits from MultiSigFactory and adds a
    # payment functionality

    class MultiSigFactoryWithPayment(MultiSigFactory):
        def __init__(self):
            MultiSigFactory.__init__(self)

        @sp.private(with_storage="read-write", with_operations=True)
        def onOK(self, contract):
            sp.send(contract.owner, contract.amount)


def addMultiSig(c, thresholdWeight, thresholdGroupsOK):
    # tgroup = c.getStorageType().go('multisigs').go('list').go('groups').go('list')
    # tparticipant = tgroup.go('participants').go('list')
    def group(contractWeight, thresholdWeight, thresholdVoters, participants):
        participants = [
            sp.record(hasVoted=False, weight=weight, id=id)
            for (id, weight) in participants
        ]
        return sp.record(
            weight=0,
            voters=0,
            contractWeight=contractWeight,
            thresholdWeight=thresholdWeight,
            thresholdVoters=thresholdVoters,
            participants=participants,
            ok=False,
        )

    p1 = sp.address("tz1NFevnqBrtcZTZTeKP2YBBjsPs9bih5i3J")
    p2 = sp.address("tz1ZRjMiF9K9n3S9AcUrTGUzR2okS7dn9KXS")
    p3 = sp.address("tz1NLJRAAwYdggijWz9EFtX5Dgs95BLfD6mP")
    g1 = group(5, 5, 2, [(p1, 2), (p2, 8), (p3, 1)])
    g2 = group(7, 5, 1, [(p1, 7), (p2, 8)])
    g3 = group(7, 10, 1, [(p3, 10)])
    contract = sp.record(
        amount=sp.tez(0),
        name="demo",
        owner=p1,
        thresholdGroupsOK=thresholdGroupsOK,
        groupsOK=0,
        thresholdWeight=thresholdWeight,
        weight=0,
        groups=sp.list([g1, g2, g3]),
        ok=False,
    )
    return c.build(contract=contract)


# Tests
@sp.add_test()
def test():
    alice = sp.test_account("Alice")
    bob = sp.test_account("Rob")
    charlie = sp.test_account("Charlie")

    scenario = sp.test_scenario("MultiSig")
    c1 = main.MultiSigFactory()
    scenario.h1("Multi Sig")
    scenario.h2("Contract")
    scenario.h3("Simple multisig factories")
    scenario += c1
    scenario.h2("First: define a simple multisig")
    addMultiSig(c1, thresholdWeight=10, thresholdGroupsOK=2)
    scenario.h2("Message execution")
    scenario.h3("A first move")
    c1.sign(id=alice.address, contractId=0, contractName="demo", _sender=alice)
    c1.sign(id=bob.address, contractId=0, contractName="demo", _sender=bob)

    scenario.h2("First: define a simple multi-sig")
    addMultiSig(c1, thresholdWeight=10, thresholdGroupsOK=3)
    scenario.h2("Message execution")
    scenario.h3("A first move")
    c1.sign(id=alice.address, contractId=1, contractName="demo", _sender=alice)
    c1.sign(id=bob.address, contractId=1, contractName="demo", _sender=bob)
    scenario.h4("We need a third vote")
    c1.sign(id=charlie.address, contractId=1, contractName="demo", _sender=charlie)
    scenario.h4("Final state")
    scenario.show(c1.data)

    scenario.h3("Multisig factories with payments")
    c2 = main.MultiSigFactoryWithPayment()
    scenario += c2
