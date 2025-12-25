import smartpy as sp


@sp.module
def main():
    # Internal administration action type specification
    InternalAdminAction: type = sp.variant(
        addSigners=sp.list[sp.address],
        changeQuorum=sp.nat,
        removeSigners=sp.list[sp.address],
    )

    class MultisigAction(sp.Contract):
        """A contract that can be used by multiple signers to administrate other
        contracts. The administrated contracts implement an interface that make it
        possible to explicit the administration process to non expert users.

        Signers vote for proposals. A proposal is a list of a target with a list of
        action. An action is a simple byte but it is intended to be a pack value of
        a variant. This simple pattern make it possible to build a UX interface
        that shows the content of a proposal or build one.
        """

        def __init__(self, quorum: sp.nat, signers: sp.set[sp.address]):
            self.data.inactiveBefore = 0
            self.data.nextId = 0
            self.data.proposals = sp.cast(
                sp.big_map(),
                sp.big_map[
                    sp.nat,
                    sp.list[sp.record(target=sp.address, actions=sp.list[sp.bytes])],
                ],
            )
            self.data.quorum = quorum
            self.data.signers = signers
            self.data.votes = sp.cast(
                sp.big_map(), sp.big_map[sp.nat, sp.set[sp.address]]
            )

        @sp.entrypoint
        def send_proposal(self, proposal):
            """Signer-only. Submit a proposal to the vote.

            Args:
                proposal (sp.list of sp.record of target address and action): List\
                    of target and associated administration actions.
            """
            assert self.data.signers.contains(sp.sender), "Only signers can propose"
            self.data.proposals[self.data.nextId] = proposal
            self.data.votes[self.data.nextId] = set()
            self.data.nextId += 1

        @sp.entrypoint
        def vote(self, pId):
            """Vote for one or more proposals

            Args:
                pId (sp.nat): Id of the proposal.
            """
            assert self.data.signers.contains(sp.sender), "Only signers can vote"
            assert self.data.votes.contains(pId), "Proposal unknown"
            assert pId >= self.data.inactiveBefore, "The proposal is inactive"
            self.data.votes[pId].add(sp.sender)

            if sp.len(self.data.votes.get(pId, default=set())) >= self.data.quorum:
                self._onApproved(pId)

        @sp.private(with_storage="read-write", with_operations=True)
        def _onApproved(self, pId):
            """Inlined function. Logic applied when a proposal has been approved."""
            proposal = self.data.proposals.get(pId, default=[])
            for p_item in proposal:
                contract = sp.contract(sp.list[sp.bytes], p_item.target)
                sp.transfer(
                    p_item.actions,
                    sp.tez(0),
                    contract.unwrap_some(error="InvalidTarget"),
                )
            # Inactivate all proposals that have been already submitted.
            self.data.inactiveBefore = self.data.nextId

        @sp.entrypoint
        def administrate(self, actions):
            """Self-call only. Administrate this contract.

            This entrypoint must be called through the proposal system.

            Args:
                actions (sp.list of sp.bytes): List of packed variant of \
                    `InternalAdminAction` (`addSigners`, `changeQuorum`, `removeSigners`).
            """
            assert (
                sp.sender == sp.self_address
            ), "This entrypoint must be called through the proposal system."

            for packed_actions in actions:
                action = sp.unpack(packed_actions, InternalAdminAction).unwrap_some(
                    error="Bad actions format"
                )
                match action:
                    case changeQuorum(quorum):
                        self.data.quorum = quorum
                    case addSigners(added):
                        for signer in added:
                            self.data.signers.add(signer)
                    case removeSigners(removed):
                        for address in removed:
                            self.data.signers.remove(address)
                # Ensure that the contract never requires more quorum than the total of signers.
                assert self.data.quorum <= sp.len(
                    self.data.signers
                ), "More quorum than signers."


if "main" in __name__:

    @sp.add_test()
    def test():
        signer1 = sp.test_account("signer1")
        signer2 = sp.test_account("signer2")
        signer3 = sp.test_account("signer3")

        s = sp.test_scenario("Basic scenario")
        s.h1("Basic scenario")

        s.h2("Origination")
        c1 = main.MultisigAction(
            quorum=2,
            signers={signer1.address, signer2.address},
        )
        s += c1

        s.h2("Proposal for adding a new signer")
        target = sp.to_address(
            sp.contract(sp.list[sp.bytes], c1.address, "administrate").unwrap_some()
        )
        action = sp.pack(
            sp.set_type_expr(
                sp.variant.addSigners([signer3.address]), main.InternalAdminAction
            )
        )
        c1.send_proposal([sp.record(target=target, actions=[action])], _sender=signer1)

        s.h2("Signer 1 votes for the proposal")
        c1.vote(0, _sender=signer1)
        s.h2("Signer 2 votes for the proposal")
        c1.vote(0, _sender=signer2)

        s.verify(c1.data.signers.contains(signer3.address))
