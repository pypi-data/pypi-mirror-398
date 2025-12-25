import smartpy as sp

"""
    A Multisig Contract used to administrate other contracts.
    THIS CONTRACT IS FOR ILLUSTRATIVE PURPOSE.
    IT HAS NOT BEEN AUDITED.
"""


@sp.module
def MS_TYPES():
    # Internal administration action type specification
    InternalAdminAction: type = sp.variant(
        changeSigners=sp.variant(
            removed=sp.set[sp.address],
            added=sp.list[sp.record(address=sp.address, publicKey=sp.key)],
        ),
        changeQuorum=sp.nat,
        changeMetadata=sp.pair[sp.string, sp.option[sp.bytes]],
    )

    # External administration action type specification
    ExternalAdminAction: type = sp.record(target=sp.address, actions=sp.bytes)

    # Proposal action type specification
    ProposalAction: type = sp.variant(
        internal=sp.list[InternalAdminAction], external=sp.list[ExternalAdminAction]
    )

    # Proposal type specification
    Proposal: type = sp.record(
        startedAt=sp.timestamp,
        initiator=sp.address,
        endorsements=sp.set[sp.address],
        actions=ProposalAction,
    )

    AggregatedProposalParams: type = sp.record(
        signatures=sp.list[sp.record(signerAddress=sp.address, signature=sp.signature)],
        proposalId=sp.nat,
        actions=ProposalAction,
    )

    AggregatedEndorsementParams: type = sp.list[
        sp.record(
            signatures=sp.list[
                sp.record(signerAddress=sp.address, signature=sp.signature)
            ],
            proposalId=sp.nat,
        )
    ]


@sp.module
def ERR():
    Badsig = "MULTISIG_Badsig"
    ProposalUnknown = "MULTISIG_ProposalUnknown"
    NotInitiator = "MULTISIG_NotInitiator"
    SignerUnknown = "MULTISIG_SignerUnknown"
    InvalidTarget = "MULTISIG_InvalidTarget"
    MoreQuorumThanSigners = "MULTISIG_MoreQuorumThanSigners"
    InvalidProposalId = "MULTISIG_InvalidProposalId"


METADATA = {
    "name": "Generic Multisig Administrator",
    "version": "1",
    "description": "Generic Multisig Administrator",
    "source": {"tools": ["SmartPy"]},
    "interfaces": ["TZIP-016"],
}


@sp.module
def main():
    import ERR
    import MS_TYPES

    @sp.effects(with_storage="read-only")
    def failIfNotSigner(address):
        sp.cast(
            self.data.signers,
            sp.map[
                sp.address,
                sp.record(publicKey=sp.key, lastProposalId=sp.option[sp.nat]),
            ],
        )
        assert self.data.signers.contains(address), ERR.SignerUnknown

    class MultisigAdmin(sp.Contract):
        def __init__(self, quorum, signers, metadata):
            # Metadata helper
            # self.init_metadata("metadata", METADATA)

            self.data.quorum = quorum
            self.data.lastProposalId = 0
            self.data.signers = signers
            self.data.proposals = sp.big_map()
            self.data.activeProposals = set()
            self.data.metadata = metadata

            sp.cast(
                self.data,
                sp.record(
                    quorum=sp.nat,
                    lastProposalId=sp.nat,
                    signers=sp.map[
                        sp.address,
                        sp.record(publicKey=sp.key, lastProposalId=sp.option[sp.nat]),
                    ],
                    proposals=sp.big_map[sp.nat, MS_TYPES.Proposal],
                    activeProposals=sp.set[sp.nat],
                    metadata=sp.big_map[sp.string, sp.bytes],
                ),
            )

        @sp.entrypoint
        def proposal(self, actions):
            """
            Each user can have at most one proposal active at a time.
            Submitting a new proposal overrides the previous one.
            """
            # Proposals can only be submitted by registered signers
            failIfNotSigner(sp.sender)

            # If the proposal initiator has an active proposal,
            # then replace that proposal with the new one
            signerLastProposalId = self.data.signers[sp.sender].lastProposalId
            match signerLastProposalId:
                case Some(id):
                    self.data.activeProposals.remove(id)

            # Increment proposal counter
            self.data.lastProposalId += 1
            proposalId = self.data.lastProposalId
            # Store new proposal
            self.data.activeProposals.add(proposalId)
            self.data.proposals[proposalId] = sp.record(
                startedAt=sp.now,
                initiator=sp.sender,
                endorsements={sp.sender},
                actions=actions,
            )
            # Update signer's last proposal
            self.data.signers[sp.sender].lastProposalId = sp.Some(proposalId)

            # Approve the proposal if quorum only requires 1 vote
            if self.data.quorum < 2:
                self.onApproved(
                    sp.record(
                        proposalId=proposalId,
                        actions=actions,
                    )
                )

        @sp.entrypoint
        def endorsement(self, endorsements):
            """
            Entrypoint used to submit endorsements to single/multiple proposals.
            """
            # Endorsements can only be submitted by registered signers
            failIfNotSigner(sp.sender)

            # Iterate over every endorsement
            for pId in endorsements:
                self.registerEndorsement(
                    sp.record(proposalId=pId, signerAddress=sp.sender)
                )

                # Approve the proposal if quorum was reached
                proposal = self.data.proposals[pId]
                if sp.len(proposal.endorsements) >= self.data.quorum:
                    self.onApproved(
                        sp.record(
                            proposalId=pId,
                            actions=proposal.actions,
                        )
                    )

        @sp.entrypoint
        def aggregated_proposal(self, params):
            """
            Users can send aggregated proposal, which are signed offchain and validated onchain.
            """
            sp.cast(params, MS_TYPES.AggregatedProposalParams)
            failIfNotSigner(sp.sender)

            self.data.lastProposalId += 1
            assert self.data.lastProposalId == params.proposalId, ERR.InvalidProposalId

            proposal = sp.record(
                startedAt=sp.now,
                initiator=sp.sender,
                endorsements={sp.sender},
                actions=params.actions,
            )

            # If the proposal initiator has an active proposal,
            # then replace that proposal with the new one
            proposerLastProposalId = self.data.signers[sp.sender].lastProposalId
            match proposerLastProposalId:
                case Some(id):
                    self.data.activeProposals.remove(id)
            self.data.signers[sp.sender].lastProposalId = sp.Some(params.proposalId)

            self.data.activeProposals.add(params.proposalId)
            self.data.proposals[params.proposalId] = proposal

            preSignature = sp.pack(
                sp.record(
                    actions=params.actions,
                    # (contractAddress + proposalId) protect against replay attacks
                    proposalId=params.proposalId,
                    # use deprecated self_address() to check warning
                    contractAddress=sp.self_address(),
                )
            )

            # Validate and apply endorsements
            for signature in params.signatures:
                failIfNotSigner(signature.signerAddress)

                publicKey = self.data.signers[signature.signerAddress].publicKey
                assert sp.check_signature(
                    publicKey, signature.signature, preSignature
                ), ERR.Badsig

                proposal.endorsements.add(signature.signerAddress)

            # Check quorum
            if sp.len(proposal.endorsements) >= self.data.quorum:
                self.onApproved(
                    sp.record(
                        proposalId=params.proposalId,
                        actions=proposal.actions,
                    )
                )

        @sp.entrypoint
        def aggregated_endorsement(self, endorsements):
            """
            Users can send aggregated votes, which are signed offchain and validated onchain.
            """
            sp.cast(endorsements, MS_TYPES.AggregatedEndorsementParams)

            for endorsement in endorsements:
                for signature in endorsement.signatures:
                    failIfNotSigner(signature.signerAddress)
                    preSignature = sp.pack(
                        sp.record(
                            # (contractAddress + proposalId) protect against replay attacks
                            contractAddress=sp.self_address,
                            proposalId=endorsement.proposalId,
                        )
                    )
                    publicKey = self.data.signers[signature.signerAddress].publicKey
                    assert sp.check_signature(
                        publicKey, signature.signature, preSignature
                    ), ERR.Badsig
                    self.registerEndorsement(
                        sp.record(
                            proposalId=endorsement.proposalId,
                            signerAddress=signature.signerAddress,
                        )
                    )
                proposal = self.data.proposals[endorsement.proposalId]
                if sp.len(proposal.endorsements) >= self.data.quorum:
                    self.onApproved(
                        sp.record(
                            proposalId=endorsement.proposalId,
                            actions=proposal.actions,
                        )
                    )

        @sp.entrypoint
        def cancel_proposal(self, proposalId):
            failIfNotSigner(sp.sender)

            # Signers can only cancel their own proposals
            assert (
                self.data.proposals[proposalId].initiator == sp.sender
            ), ERR.NotInitiator
            self.data.activeProposals.remove(proposalId)

        @sp.private(with_storage="read-write")
        def registerEndorsement(self, params):
            assert self.data.activeProposals.contains(
                params.proposalId
            ), ERR.ProposalUnknown
            # Add endorsement to proposal
            self.data.proposals[params.proposalId].endorsements.add(
                params.signerAddress
            )

        @sp.private(with_storage="read-write", with_operations=True)
        def onApproved(self, params):
            match params.actions:
                # Internal actions are applied to the multisig contract
                case internal(internalActions):
                    for action in internalActions:
                        match action:
                            case changeQuorum(quorum):
                                self.data.quorum = quorum
                            case changeMetadata(metadata):
                                (k, v) = metadata
                                if v.is_some():
                                    self.data.metadata[k] = v.unwrap_some()
                                else:
                                    del self.data.metadata[k]

                            case changeSigners(changeSigners):
                                match changeSigners:
                                    case removed(removeSet):
                                        for address in removeSet.elements():
                                            if self.data.signers.contains(address):
                                                # Remove signer
                                                del self.data.signers[address]
                                                # We don't remove signer[address].lastProposalId
                                                # because we remove all activeProposals after it.
                                    case added(addList):
                                        for signer in addList:
                                            self.data.signers[signer.address] = (
                                                sp.record(
                                                    publicKey=signer.publicKey,
                                                    lastProposalId=None,
                                                )
                                            )
                        # Ensure that the contract never requires more quorum than the total of signers.
                        assert self.data.quorum <= sp.len(
                            self.data.signers
                        ), ERR.MoreQuorumThanSigners
                    # Removes all active proposals after an administrative change.
                    self.data.activeProposals = set()
                # External actions are applied to other contracts
                case external(externalActions):
                    for action in externalActions:
                        target = sp.contract(sp.bytes, action.target).unwrap_some(
                            error=ERR.InvalidTarget
                        )
                        sp.transfer(action.actions, sp.tez(0), target)

            self.data.activeProposals.remove(params.proposalId)


@sp.module
def helpers():
    AdministrationType: type = sp.variant(changeAdmin=sp.address, changeActive=sp.bool)

    class Administrated(sp.Contract):
        """
        This contract is a sample
        It shows how a contract can be administrated
        through the multisig administration contract
        """

        def __init__(self, admin, active):
            self.data.admin = admin
            self.data.active = active

        @sp.entrypoint
        def administrate(self, actionsBytes):
            assert sp.sender == self.data.admin, "NOT ADMIN"

            # actionsBytes is packed and must be unpacked
            actions = sp.unpack(actionsBytes, sp.list[AdministrationType]).unwrap_some(
                error="Actions are invalid"
            )

            for action in actions:
                match action:
                    case changeActive(active):
                        self.data.active = active
                    case changeAdmin(admin):
                        self.data.admin = admin

        @sp.entrypoint
        def verifyActive(self):
            assert self.data.active, "NOT ACTIVE"


if "main" in __name__:
    #########
    # Helpers

    class InternalHelper:
        def variant(content):
            return sp.variant.internal(content)

        def changeQuorum(quorum):
            return sp.variant.changeQuorum(quorum)

        def removeSigners(l):
            sp.cast(l, sp.set[sp.address])
            return sp.variant.changeSigners(sp.variant.removed(l))

        def addSigners(l):
            added_list = []
            for added_info in l:
                addr, publicKey = added_info
                added_list.append(sp.record(address=addr, publicKey=publicKey))
            return sp.variant.changeSigners(sp.variant.added(sp.list(added_list)))

    class ExternalHelper:
        def variant(content):
            return sp.variant.external(content)

        def changeActive(active):
            return sp.variant.changeActive(active)

        def changeAdmin(address):
            return sp.variant.changeAdmin(address)

    def sign(account, contract):
        message = sp.pack(
            sp.record(
                contractAddress=contract.address,
                proposalId=contract.data.lastProposalId,
            )
        )
        signature = sp.make_signature(account.secret_key, message, message_format="Raw")
        vote = sp.record(signerAddress=account.address, signature=signature)
        return vote

    def packActions(actions):
        actions = sp.set_type_expr(actions, sp.list[helpers.AdministrationType])
        return sp.pack(actions)

    def add_test(internal_tests):
        name = (
            "Internal Administration tests"
            if internal_tests
            else "External Administration tests"
        )

        @sp.add_test()
        def test():
            sc = sp.test_scenario(name, [main, helpers])
            sc.h1(name)

            admin = sp.test_account("admin")
            signer1 = sp.test_account("signer1")
            signer2 = sp.test_account("signer2")
            signer3 = sp.test_account("signer3")
            signer4 = sp.test_account("signer4")

            simulation_mode = sc.simulation_mode()

            if internal_tests:
                sc.h3("Originate Multisig Admin")
                multisigAdmin = main.MultisigAdmin(
                    quorum=1,
                    signers=sp.map(
                        {
                            signer1.address: sp.record(
                                publicKey=signer1.public_key, lastProposalId=None
                            ),
                            signer2.address: sp.record(
                                publicKey=signer2.public_key, lastProposalId=None
                            ),
                        }
                    ),
                    metadata=sp.scenario_utils.metadata_of_url("ipfs://"),
                )
                sc += multisigAdmin

                ##########################
                # Auto-accepted proposal #
                ##########################
                sc.h2("Auto-accepted proposal when quorum is 1")
                sc.h3("signer1 propose to change quorum to 2")
                sc.verify(multisigAdmin.data.quorum == 1)
                changeQuorum = InternalHelper.changeQuorum(2)
                multisigAdmin.proposal(
                    InternalHelper.variant([changeQuorum]), _sender=signer1
                )
                sc.verify(multisigAdmin.data.quorum == 2)

                ####################
                # Add a 3rd signer #
                ####################
                sc.h2("Adding a 3rd signer")
                sc.h3("signer2 new proposal to include signer3")
                sc.verify(sp.len(multisigAdmin.data.signers) == 2)
                sc.verify(~multisigAdmin.data.signers.contains(signer3.address))
                changeSigners = InternalHelper.addSigners(
                    [(signer3.address, signer3.public_key)]
                )
                multisigAdmin.proposal(
                    InternalHelper.variant([changeSigners]), _sender=signer2
                )
                sc.h3("signer1 votes the proposal")
                multisigAdmin.endorsement(
                    [multisigAdmin.data.lastProposalId], _sender=signer1
                )
                sc.verify(multisigAdmin.data.signers.contains(signer3.address))
                sc.verify(sp.len(multisigAdmin.data.signers) == 3)

                ############################################
                # New proposal (change Quorum from 2 to 3) #
                ############################################
                sc.h2("New proposal (change Quorum from 2 to 3)")
                sc.h3("signer1 new proposal to change quorum to 3")
                changeQuorum = InternalHelper.changeQuorum(3)
                multisigAdmin.proposal(
                    InternalHelper.variant([changeQuorum]), _sender=signer1
                )
                # Proposal has not been validated yet
                sc.verify(multisigAdmin.data.quorum == 2)
                sc.h3("signer2 votes the proposal (2/2)")
                multisigAdmin.endorsement(
                    [multisigAdmin.data.lastProposalId], _sender=signer2
                )
                sc.verify(multisigAdmin.data.quorum == 3)

                ###########################################
                # Newly included signer starts a proposal #
                ###########################################
                sc.h2("Newly included signer starts a proposal")
                sc.h3("New proposal by signer 3 to decrease quorum to 2")
                changeQuorum = InternalHelper.changeQuorum(2)
                multisigAdmin.proposal(
                    InternalHelper.variant([changeQuorum]), _sender=signer3
                )
                sc.h3("signer1 votes the proposal")
                multisigAdmin.endorsement(
                    [multisigAdmin.data.lastProposalId], _sender=signer1
                )
                sc.verify(multisigAdmin.data.quorum == 3)
                sc.h3("signer2 votes the proposal")
                multisigAdmin.endorsement(
                    [multisigAdmin.data.lastProposalId], _sender=signer2
                )
                sc.verify(multisigAdmin.data.quorum == 2)

                ##########
                # Cancel #
                ##########
                sc.h2("Proposal cancellation")
                sc.h3("New proposal by signer 1")
                changeTimeout = InternalHelper.changeQuorum(3)
                multisigAdmin.proposal(
                    InternalHelper.variant([changeTimeout]), _sender=signer1
                )
                sc.verify(sp.len(multisigAdmin.data.activeProposals) == 1)
                sc.h3(
                    "Signer 2 tries to cancel the proposal (must fail, only the initiator can cancel)"
                )
                multisigAdmin.cancel_proposal(
                    multisigAdmin.data.lastProposalId, _sender=signer2, _valid=False
                )
                sc.h3("Signer 1 cancels the proposal")
                multisigAdmin.cancel_proposal(
                    multisigAdmin.data.lastProposalId, _sender=signer1
                )
                sc.verify(sp.len(multisigAdmin.data.activeProposals) == 0)
                sc.h3("Signer 2 tries to vote the canceled proposal")
                multisigAdmin.endorsement(
                    [multisigAdmin.data.lastProposalId], _sender=signer2, _valid=False
                )
                sc.verify(multisigAdmin.data.quorum != 3)

                ######################
                # 2 actions proposal #
                ######################
                sc.h2("2 actions proposal")
                sc.h3("Signer 1 new proposal: change quorum to 2 and add signer 4")
                sc.verify(~multisigAdmin.data.signers.contains(signer4.address))
                changeQuorum = InternalHelper.changeQuorum(3)
                changeSigners = InternalHelper.addSigners(
                    [(signer4.address, signer4.public_key)]
                )
                multisigAdmin.proposal(
                    InternalHelper.variant([changeQuorum, changeSigners]),
                    _sender=signer1,
                )
                sc.h3("Signer 2 votes the proposal")
                multisigAdmin.endorsement(
                    [multisigAdmin.data.lastProposalId], _sender=signer2
                )
                sc.verify(multisigAdmin.data.quorum == 3)
                sc.verify(multisigAdmin.data.signers.contains(signer4.address))

                #########################################
                # 2 Internal proposals at the same time #
                #########################################
                sc.h3("Signer 1 new proposal: change quorum to 2 and remove signer 4")
                changeQuorum = InternalHelper.changeQuorum(2)
                multisigAdmin.proposal(
                    InternalHelper.variant([changeQuorum]), _sender=signer1
                )
                changeSigners = InternalHelper.removeSigners({signer4.address})
                multisigAdmin.proposal(
                    InternalHelper.variant([changeSigners]), _sender=signer2
                )
                sc.verify(sp.len(multisigAdmin.data.activeProposals) == 2)
                sc.h3("Signer 3 votes on quorum proposal")
                multisigAdmin.endorsement(
                    [sp.as_nat(multisigAdmin.data.lastProposalId - 1)], _sender=signer3
                )
                sc.h3("Signer 4 votes on signers proposal")
                multisigAdmin.endorsement(
                    [multisigAdmin.data.lastProposalId], _sender=signer4
                )
                sc.h3("Confirm that nothing has changed")
                sc.verify(multisigAdmin.data.quorum == 3)
                sc.verify(multisigAdmin.data.signers.contains(signer4.address))
                sc.h3("Signer 4 votes on quorum proposal")
                multisigAdmin.endorsement(
                    [sp.as_nat(multisigAdmin.data.lastProposalId - 1)], _sender=signer4
                )
                sc.h3(
                    "Confirm that quorum was updated and signers proposal was canceled"
                )
                sc.verify(sp.len(multisigAdmin.data.activeProposals) == 0)
                sc.verify(multisigAdmin.data.quorum == 2)
                sc.verify(multisigAdmin.data.signers.contains(signer4.address))

                #########################
                # Multisig endorsements #
                #########################
                sc.h2("Multi vote in one call")
                sc.h3("Signer 1 new proposal")
                changeQuorum = InternalHelper.changeQuorum(3)
                multisigAdmin.proposal(
                    InternalHelper.variant([changeQuorum]), _sender=signer1
                )
                if simulation_mode is sp.SimulationMode.MOCKUP:
                    # mockups error: unknown attr: secret key
                    sc.p("mockups: cant have secret keys in contracts")
                    return

                sc.h3("Signer 2 and Signer 3 votes are pushed by Signer 1")
                signer2_endorsement = sign(signer2, contract=multisigAdmin)
                signer3_endorsement = sign(signer3, contract=multisigAdmin)
                proposalEndorsements = sp.record(
                    proposalId=multisigAdmin.data.lastProposalId,
                    signatures=[signer2_endorsement, signer3_endorsement],
                )
                multisigAdmin.aggregated_endorsement(
                    [proposalEndorsements], _sender=signer1
                )
                sc.verify(multisigAdmin.data.quorum == 3)

                #####################
                # Multisig proposal #
                #####################
                sc.h2("Multi vote in one call")
                sc.h3("Signer 1 new proposal")
                changeQuorum = InternalHelper.changeQuorum(3)
                multisigAdmin.proposal(
                    InternalHelper.variant([changeQuorum]), _sender=signer1
                )
                sc.h3("Signer 2 and Signer 3 votes are pushed by Signer 1")
                signer2_vote = sign(signer2, contract=multisigAdmin)
                signer3_vote = sign(signer3, contract=multisigAdmin)
                proposalVotes = sp.record(
                    proposalId=multisigAdmin.data.lastProposalId,
                    signatures=[signer2_vote, signer3_vote],
                )
                multisigAdmin.aggregated_endorsement([proposalVotes], _sender=signer1)
                sc.verify(multisigAdmin.data.quorum == 3)

            ##########################################

            else:
                sc.h3("Originate Multisig Admin")
                multisigAdmin = main.MultisigAdmin(
                    quorum=3,
                    signers=sp.map(
                        {
                            signer1.address: sp.record(
                                publicKey=signer1.public_key, lastProposalId=None
                            ),
                            signer2.address: sp.record(
                                publicKey=signer2.public_key, lastProposalId=None
                            ),
                            signer3.address: sp.record(
                                publicKey=signer3.public_key, lastProposalId=None
                            ),
                        }
                    ),
                    metadata=sp.scenario_utils.metadata_of_url("ipfs://"),
                )
                sc += multisigAdmin

                sc.h3("Originate administrated contract")
                administrated = helpers.Administrated(admin.address, False)
                sc += administrated
                administrated_entrypoint = sp.contract(
                    sp.bytes, administrated.address, entrypoint="administrate"
                ).unwrap_some()

                sc.h2("Set multisig as admin of administrated contract")
                sc.verify(administrated.data.active == False)
                sc.verify(administrated.data.admin == admin.address)
                actions = packActions(
                    [ExternalHelper.changeAdmin(multisigAdmin.address)]
                )
                administrated.administrate(actions, _sender=admin)
                sc.verify(administrated.data.active == False)
                sc.verify(administrated.data.admin == multisigAdmin.address)

                sc.h2("Activate the administrated contract")
                sc.h3("Signer 1 new proposal: changeActive")
                actions = packActions([ExternalHelper.changeActive(True)])
                multisigAdmin.proposal(
                    ExternalHelper.variant(
                        [
                            sp.record(
                                target=sp.to_address(administrated_entrypoint),
                                actions=actions,
                            )
                        ]
                    ),
                    _sender=signer1,
                )
                sc.verify(administrated.data.active == False)
                sc.h3("Signer 2 votes")
                multisigAdmin.endorsement(
                    [multisigAdmin.data.lastProposalId], _sender=signer2
                )
                sc.verify(administrated.data.active == False)
                sc.h3("Signer 3 votes")
                multisigAdmin.endorsement(
                    [multisigAdmin.data.lastProposalId], _sender=signer3
                )
                sc.verify(administrated.data.active == True)

                sc.h2("Use Multisig vote to deactivate the administrated contract")
                sc.h3("Signer 1 new proposal: changeActive")
                actions = packActions([ExternalHelper.changeActive(False)])
                multisigAdmin.proposal(
                    ExternalHelper.variant(
                        [
                            sp.record(
                                target=sp.to_address(administrated_entrypoint),
                                actions=actions,
                            )
                        ]
                    ),
                    _sender=signer1,
                )
                sc.verify(administrated.data.active == True)
                if simulation_mode is sp.SimulationMode.MOCKUP:
                    # mockups error: unknown attr: secret key
                    sc.p("mockups: cant have secret keys in contracts")
                    return

                sc.h3("Signer 2 and Signer 3 votes are pushed by Signer 1")
                signer2_vote = sign(signer2, contract=multisigAdmin)
                signer3_vote = sign(signer3, contract=multisigAdmin)
                proposalVotes = sp.record(
                    proposalId=multisigAdmin.data.lastProposalId,
                    signatures=[signer2_vote, signer3_vote],
                )
                multisigAdmin.aggregated_endorsement([proposalVotes], _sender=signer1)
                sc.verify(administrated.data.active == False)

    add_test(internal_tests=True)
    add_test(internal_tests=False)
