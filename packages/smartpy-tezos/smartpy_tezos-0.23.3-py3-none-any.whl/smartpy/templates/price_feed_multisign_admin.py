import smartpy as sp

"""
    Multisign Admin is a multisign administration contract.

    Multiple signers can propose and vote for a list of batch of actions
    on the contract itself or the target.

    The contract is configurable at origination time to adapt to target needed.

    The contract supports gathering off-chain signed votes and pushing them in one call.

    Voting system:
        When the quorum is reached on a proposal,
        If the number of yay > nay: the proposal is acceped
        Else: the proposal is rejected

        Once a proposal is accepted the batchs of actions are executed,
        the other proposals are automatically canceled.

    Vocabulary:
        Action: something to do on the MultisignAdmin or Target
        Batch of Actions: multiple actions to do on the same internal call
        List of Batchs: multiple internal calls containing batch of actions

    A complexe proposal can include for example 2 batchs of actions:
    1) Self admin: change quorum + change signers
    2) Target admin: change parameter + change active

    Antipattern:
        Instead of doing 2 batchs of 2 actions
        some could be tempted to use 4 batchs of 1 action
        In this case the params will be bigger and there will be 2 internal calls.
        Advice: Use less batchs possible and most actions per batch
"""


@sp.module
def m2():
    # TODO: activate when metadata is available
    # AGGREGATOR_METADATA = {
    #     "name"          : "Multi-sign Administrator",
    #     "version"       : "1",
    #     "description"   : "Multi-sign administrator for the price feed aggregator",
    #     "source"        : {
    #         "tools": [ "SmartPy" ]
    #     },
    #     "interfaces"    : [ "TZIP-016" ],
    # }

    MultisignAdmin_Badsig = "MultisignAdmin_Badsig"
    MultisignAdmin_ProposalClosed = "MultisignAdmin_ProposalClosed"
    MultisignAdmin_ProposalUnknown = "MultisignAdmin_ProposalUnknown"
    MultisignAdmin_AlreadyVoted = "MultisignAdmin_AlreadyVoted"
    MultisignAdmin_VoterUnknown = "MultisignAdmin_VoterUnknown"
    MultisignAdmin_VoterAlreadyknown = "MultisignAdmin_VoterAlreadyknown"
    MultisignAdmin_ProposalTimedout = "MultisignAdmin_ProposalTimedout"
    MultisignAdmin_TargetUnkown = "MultisignAdmin_TargetUnkown"
    MultisignAdmin_MoreQuorumThanVoters = "MultisignAdmin_MoreQuorumThanVoters"
    MultisignAdmin_VotersLessThan1 = "MultisignAdmin_VotersLessThan1"
    MultisignAdmin_TargetNotSet = "MultisignAdmin_TargetNotSet"
    MultisignAdmin_WrongCallbackInterface = "MultisignAdmin_WrongCallbackInterface"

    t_selfAdminAction: type = sp.variant(
        changeVoters=sp.record(
            removed=sp.set[sp.address],
            added=sp.list[sp.record(addr=sp.address, publicKey=sp.key)],
        ),
        changeTarget=sp.address,
        changeQuorum=sp.nat,
        changeTimeout=sp.int,
    )

    t_targetAdminAction: type = sp.variant(
        changeOracles=sp.record(
            removed=sp.list[sp.address],
            added=sp.list[
                sp.pair[
                    sp.address,
                    sp.record(
                        startingRound=sp.nat,
                        endingRound=sp.option[sp.nat],
                        adminAddress=sp.address,
                    ),
                ]
            ],
        ),
        changeActive=sp.bool,
        changeAdmin=sp.address,
        updateFutureRounds=sp.record(
            minSubmissions=sp.nat,
            maxSubmissions=sp.nat,
            restartDelay=sp.nat,
            timeout=sp.nat,
            oraclePayment=sp.nat,
        ),
    )
    t_ProposalBatchs: type = sp.variant(
        selfAdmin=sp.list[t_selfAdminAction], targetAdmin=sp.list[t_targetAdminAction]
    )
    t_Proposal: type = sp.record(
        startedAt=sp.timestamp,
        id=sp.nat,
        yay=sp.set[sp.nat],
        nay=sp.set[sp.nat],
        batchs=sp.list[t_ProposalBatchs],
        canceled=sp.bool,
    )

    t_votes: type = sp.list[
        sp.record(voterId=sp.nat, signature=sp.signature, yay=sp.bool)
    ]

    t_proposalsVotes: type = sp.list[
        sp.record(initiatorId=sp.nat, proposalId=sp.nat, votes=t_votes)
    ]

    t_activeProposal: type = sp.record(
        startedAt=sp.timestamp,
        initiatorId=sp.nat,
        initiatorProposalId=sp.nat,
        yay=sp.set[sp.nat],
        nay=sp.set[sp.nat],
        batchs=sp.list[t_ProposalBatchs],
    )

    class MultisignAdmin(sp.Contract):
        """
        Each user can have at most one proposal
        """

        def __init__(
            self,
            quorum,
            timeout,
            addrVoterId,
            keyVoterId,
            voters,
            lastVoterId,
            metadata,
        ):
            # TODO: activate when metadata is available
            # self.init_metadata("metadata", {
            #     **AGGREGATOR_METADATA,
            #     "views": [self.listActiveProposals]
            # })

            self.data.target = None
            self.data.quorum = quorum
            self.data.timeout = timeout
            self.data.lastVoterId = lastVoterId
            self.data.lastVoteTimestamp = sp.timestamp(0)
            self.data.nbVoters = sp.len(voters)
            self.data.voters = sp.big_map()
            self.data.addrVoterId = addrVoterId
            self.data.keyVoterId = keyVoterId
            self.data.proposals = sp.big_map()
            self.data.metadata = metadata

            for voter in voters.items():
                self.data.voters[voter.key] = voter.value

            sp.cast(
                self.data,
                sp.record(
                    target=sp.option[sp.address],
                    quorum=sp.nat,
                    timeout=sp.int,
                    lastVoterId=sp.nat,
                    lastVoteTimestamp=sp.timestamp,
                    nbVoters=sp.nat,
                    voters=sp.big_map[
                        sp.nat,
                        sp.record(
                            publicKey=sp.key, addr=sp.address, lastProposalId=sp.nat
                        ),
                    ],
                    addrVoterId=sp.big_map[sp.address, sp.nat],
                    keyVoterId=sp.big_map[sp.key, sp.nat],
                    proposals=sp.big_map[sp.nat, t_Proposal],
                    metadata=sp.big_map[sp.string, sp.bytes],
                ),
            )

        # ----------------
        # Public entrypoints

        @sp.entrypoint
        def newProposal(self, batchs):
            voterId = self.data.addrVoterId.get(
                sp.sender, error=MultisignAdmin_VoterUnknown
            )
            self.data.voters[voterId].lastProposalId += 1
            self.data.proposals[voterId] = sp.record(
                startedAt=sp.now,
                id=self.data.voters[voterId].lastProposalId,
                yay={voterId},
                nay=set(),
                batchs=batchs,
                canceled=False,
            )
            if self.data.quorum < 2:
                self.onVoted(self.data.proposals[voterId])

        @sp.entrypoint
        def vote(self, votes):
            voterId = self.data.addrVoterId.get(
                sp.sender, error=MultisignAdmin_VoterUnknown
            )
            for vote in votes:
                self.registerVote(
                    sp.record(
                        initiatorId=vote.initiatorId,
                        proposalId=vote.proposalId,
                        voterId=voterId,
                        yay=vote.yay,
                    )
                )
                proposal = self.data.proposals[vote.initiatorId]
                if sp.len(proposal.nay) + sp.len(proposal.yay) >= self.data.quorum:
                    if sp.len(proposal.nay) >= sp.len(proposal.yay):
                        self.data.proposals[vote.initiatorId].canceled = True
                    else:
                        self.onVoted(proposal)

        @sp.entrypoint
        def multiVote(self, proposalsVotes):
            """
            Signed: Pair(ADDRESS multisignAdmin, Pair(initiatorId, proposalId))
            """
            sp.cast(proposalsVotes, t_proposalsVotes)
            for proposalVotes in proposalsVotes:
                initiatorId = proposalVotes.initiatorId
                proposalId = proposalVotes.proposalId
                for vote in proposalVotes.votes:
                    signed = sp.pack((sp.self_address, (initiatorId, proposalId)))
                    publicKey = self.data.voters.get(
                        vote.voterId, error=MultisignAdmin_VoterUnknown
                    ).publicKey
                    assert sp.check_signature(
                        publicKey, vote.signature, signed
                    ), MultisignAdmin_Badsig
                    self.registerVote(
                        sp.record(
                            initiatorId=initiatorId,
                            proposalId=proposalId,
                            voterId=vote.voterId,
                            yay=vote.yay,
                        )
                    )
                proposal = self.data.proposals[initiatorId]
                if sp.len(proposal.nay) + sp.len(proposal.yay) >= self.data.quorum:
                    if sp.len(proposal.nay) >= sp.len(proposal.yay):
                        self.data.proposals[initiatorId].canceled = True
                    else:
                        self.onVoted(proposal)

        @sp.entrypoint
        def cancelProposal(self, proposalId):
            voterId = self.data.addrVoterId.get(
                sp.sender, error=MultisignAdmin_VoterUnknown
            )
            proposal = self.data.proposals.get(
                voterId, error=MultisignAdmin_ProposalUnknown
            )
            assert proposal.id == proposalId, MultisignAdmin_ProposalUnknown
            self.data.proposals[voterId].canceled = True

        # ----------------
        # Public views
        @sp.entrypoint
        def getParams(self, callback):
            params = sp.record(
                target=self.data.target,
                quorum=self.data.quorum,
                timeout=self.data.timeout,
            )
            sp.transfer(params, sp.tez(0), callback)

        @sp.entrypoint
        def getLastProposal(self, params):
            proposal = self.data.proposals[sp.fst(params)]
            callback = sp.contract(t_Proposal, sp.snd(params))
            sp.transfer(
                proposal,
                sp.tez(0),
                callback.unwrap_some(error=MultisignAdmin_WrongCallbackInterface),
            )

        # ----------------
        # Offchain views

        @sp.offchain_view
        def listActiveProposals(self):
            """List active proposals"""
            proposals = self.data.proposals
            response = sp.cast([], sp.list[t_activeProposal])

            for voterId in range(0, self.data.nbVoters, 1):
                if proposals.contains(voterId):
                    proposal = proposals[voterId]
                    if (
                        # not canceled
                        not proposal.canceled
                        # not timedout
                        and sp.now
                        < sp.add_seconds(proposal.startedAt, self.data.timeout * 60)
                        # not already voted
                        and (sp.len(proposal.nay) + sp.len(proposal.yay))
                        < self.data.quorum
                        # not closed by other vote
                        and proposal.startedAt > self.data.lastVoteTimestamp
                    ):
                        response.push(
                            sp.record(
                                startedAt=proposal.startedAt,
                                initiatorId=voterId,
                                initiatorProposalId=proposal.id,
                                yay=proposal.yay,
                                nay=proposal.nay,
                                batchs=proposal.batchs,
                            )
                        )

            return response

        # ----------------
        # Private functions

        @sp.private(with_storage="read-write")
        def registerVote(self, params):
            proposal = self.data.proposals.get(
                params.initiatorId, error=MultisignAdmin_ProposalUnknown
            )
            assert proposal.id == params.proposalId, MultisignAdmin_ProposalUnknown
            assert (
                proposal.startedAt > self.data.lastVoteTimestamp
                and not proposal.canceled
            ), MultisignAdmin_ProposalClosed
            assert sp.now < sp.add_seconds(
                proposal.startedAt, self.data.timeout * 60
            ), MultisignAdmin_ProposalTimedout
            assert not proposal.yay.contains(
                params.voterId
            ) and not proposal.nay.contains(params.voterId), MultisignAdmin_AlreadyVoted
            if params.yay:
                proposal.yay.add(params.voterId)
            else:
                proposal.nay.add(params.voterId)
            self.data.proposals[params.initiatorId] = proposal

        @sp.private(with_storage="read-write", with_operations=True)
        def onVoted(self, proposal):
            self.data.lastVoteTimestamp = sp.now
            for batch in proposal.batchs:
                match batch:
                    case selfAdmin(selfAdminActions):
                        for action in selfAdminActions:
                            match action:
                                case changeQuorum(quorum):
                                    assert (
                                        quorum <= self.data.nbVoters
                                    ), MultisignAdmin_MoreQuorumThanVoters
                                    self.data.quorum = quorum
                                case changeTarget(target):
                                    self.data.target = sp.Some(target)
                                case changeTimeout(timeout):
                                    self.data.timeout = timeout
                                case changeVoters(changeVoters):
                                    for voterAddress in changeVoters.removed.elements():
                                        voterId = self.data.addrVoterId.get(
                                            voterAddress,
                                            error=MultisignAdmin_VoterUnknown,
                                        )
                                        del self.data.addrVoterId[voterAddress]
                                        del self.data.keyVoterId[
                                            self.data.voters[voterId].publicKey
                                        ]
                                        del self.data.proposals[voterId]
                                        del self.data.voters[voterId]
                                    self.data.nbVoters = sp.as_nat(
                                        self.data.nbVoters
                                        - sp.len(changeVoters.removed)
                                    )
                                    for voter in changeVoters.added:
                                        assert not self.data.addrVoterId.contains(
                                            voter.addr
                                        ) and not self.data.keyVoterId.contains(
                                            voter.publicKey
                                        ), MultisignAdmin_VoterAlreadyknown
                                        self.data.lastVoterId += 1
                                        voterId = self.data.lastVoterId
                                        self.data.voters[voterId] = sp.record(
                                            publicKey=voter.publicKey,
                                            addr=voter.addr,
                                            lastProposalId=0,
                                        )
                                        self.data.addrVoterId[voter.addr] = voterId
                                        self.data.keyVoterId[voter.publicKey] = voterId
                                    self.data.nbVoters += sp.len(changeVoters.added)
                                    assert (
                                        self.data.nbVoters > 0
                                    ), MultisignAdmin_VotersLessThan1
                                    assert (
                                        self.data.quorum <= self.data.nbVoters
                                    ), MultisignAdmin_MoreQuorumThanVoters
                    case targetAdmin(targetActions):
                        target = self.data.target.unwrap_some(
                            error=MultisignAdmin_TargetNotSet
                        )
                        target_contract = sp.contract(
                            sp.list[t_targetAdminAction], target
                        ).unwrap_some(error=MultisignAdmin_TargetUnkown)
                        sp.transfer(targetActions, sp.tez(0), target_contract)

    ################
    # Test contract

    class Administrated(sp.Contract):
        """
        This contract is a sample
        It shouws how a contract can be administrated
        through the multisign administration contract
        """

        def __init__(self, admin, active):
            self.data.admin = admin
            self.data.active = active
            self.data.value = None

            sp.cast(
                self.data,
                sp.record(
                    admin=sp.address,
                    active=sp.bool,
                    value=sp.option[sp.int],
                ),
            )

        @sp.entrypoint
        def administrate(self, actions):
            assert sp.sender == self.data.admin, "NOT ADMIN"
            sp.cast(actions, sp.list[t_targetAdminAction])
            for action in actions:
                match action:
                    case changeActive(active):
                        self.data.active = active
                    case changeAdmin(admin):
                        self.data.admin = admin

        @sp.entrypoint
        def setValue(self, value):
            assert self.data.active, "NOT ACTIVE"
            self.data.value = value


#########
# Helpers


class SelfHelper:
    def variant(content):
        return sp.variant.selfAdmin(content)

    def changeQuorum(quorum):
        return SelfHelper.variant([sp.variant.changeQuorum(quorum)])

    def changeAdmin(admin):
        return SelfHelper.variant([sp.variant.changeAdmin(admin)])

    def changeTarget(target):
        return SelfHelper.variant([sp.variant.changeTarget(target)])

    def changeTimeout(timeout):
        return SelfHelper.variant([sp.variant.changeTimeout(timeout)])

    def changeVoters(removed=[], added=[]):
        added_list = []
        for added_info in added:
            addr, publicKey = added_info
            added_list.append(sp.record(addr=addr, publicKey=publicKey))
        return SelfHelper.variant(
            [
                sp.variant(
                    "changeVoters",
                    sp.record(removed=sp.set(removed), added=sp.list(added_list)),
                )
            ]
        )


def sign(account, contract, voterId, initiatorId, proposalId, yay):
    message = sp.pack(sp.pair(contract.address, sp.pair(initiatorId, proposalId)))
    signature = sp.make_signature(account.secret_key, message, message_format="Raw")
    vote = sp.record(voterId=voterId, signature=signature, yay=yay)
    return vote


def vote(contract, signer, yay):
    """
    Only use for test as you can't know if the proposalId correspond to
    the one you want to vote
    """
    voterId = contract.data.addrVoterId[signer.address]
    proposal = contract.data.proposals[voterId]
    return sp.record(proposalId=proposal.id, initiatorId=voterId, yay=yay)


################
# Tests


def add_test(name):
    @sp.add_test()
    def test():
        sc = sp.test_scenario(name, m2)
        sc.h1(name)

        admin = sp.test_account("admin")
        signer1 = sp.test_account("signer1")
        signer2 = sp.test_account("signer2")
        signer3 = sp.test_account("signer3")
        signer4 = sp.test_account("signer4")

        sc.h2("Init contracts")

        sc.h3("Administrated")
        administrated = m2.Administrated(admin.address, False)
        sc += administrated
        administrated_entrypoint = sp.to_address(
            sp.contract(
                m2.t_targetAdminAction, administrated.address, entrypoint="administrate"
            ).unwrap_some()
        )

        sc.h3("multisignAdmin")
        multisignAdmin = m2.MultisignAdmin(
            quorum=1,
            timeout=5,
            addrVoterId=sp.big_map({signer1.address: 0, signer2.address: 1}),
            keyVoterId=sp.big_map({signer1.public_key: 0, signer2.public_key: 1}),
            voters={
                0: sp.record(
                    addr=signer1.address, publicKey=signer1.public_key, lastProposalId=0
                ),
                1: sp.record(
                    addr=signer2.address, publicKey=signer2.public_key, lastProposalId=0
                ),
            },
            lastVoterId=1,
            metadata=sp.scenario_utils.metadata_of_url(
                "ipfs://QmYnU2jwq4XU4jwX1Rmu1EGfmyhMhpDCpPpHF5j9jF9y1w"
            ),
        )
        sc += multisignAdmin

        if sc.simulation_mode() is sp.SimulationMode.MOCKUP:
            sc.p("timestamp doesnt work in mockups")
            return

        now = sp.timestamp(1)

        if name == "Self Administration tests":
            ##########################
            # Auto-accepted proposal #
            ##########################
            sc.h2("Auto-accepted proposal when quorum is 1")
            sc.h3("signer1 propose to change quorum to 2")
            sc.verify(multisignAdmin.data.quorum == 1)
            changeQuorum = SelfHelper.changeQuorum(2)
            multisignAdmin.newProposal([changeQuorum], _sender=signer1, _now=now)
            now = now.add_seconds(1)
            sc.verify(multisignAdmin.data.quorum == 2)

            ##################
            # Invalid quorum #
            ##################
            sc.h2("Invalid quorum proposal")
            sc.h3("signer1 new proposal to change quorum to 3")
            sc.verify(multisignAdmin.data.quorum != 3)
            changeQuorum = SelfHelper.changeQuorum(3)
            multisignAdmin.newProposal([changeQuorum], _sender=signer1, _now=now)
            # Proposal has not been validated yet
            sc.verify(multisignAdmin.data.quorum == 2)
            sc.h3("signer2 votes the proposal")
            sc.p("proposal is rejected because nbSigners < proposed quorum")
            multisignAdmin.vote(
                [vote(multisignAdmin, signer1, yay=True)],
                _sender=signer2,
                _valid=False,
            )
            sc.verify(multisignAdmin.data.quorum != 3)

            ##############
            # Add signer #
            ##############
            sc.h2("Adding new voters")
            sc.h3("signer2 new proposal to include signer3")
            sc.verify(~multisignAdmin.data.voters.contains(2))
            changeVoters = SelfHelper.changeVoters(
                [], added=[(signer3.address, signer3.public_key)]
            )
            multisignAdmin.newProposal([changeVoters], _sender=signer2, _now=now)
            sc.h3("signer1 votes the proposal")
            multisignAdmin.vote(
                [vote(multisignAdmin, signer2, yay=True)], _sender=signer1
            )
            sc.verify(multisignAdmin.data.voters.contains(2))
            now = now.add_seconds(1)

            #########################
            # Newly included signer #
            #########################
            sc.h2("Newly included signer starts a proposal")
            sc.h3("New proposal by signer 3 to increase quorum to 3")
            sc.verify(multisignAdmin.data.quorum != 3)
            changeQuorum = SelfHelper.changeQuorum(3)
            multisignAdmin.newProposal([changeQuorum], _sender=signer3, _now=now)
            sc.h3("signer1 votes the proposal")
            multisignAdmin.vote(
                [vote(multisignAdmin, signer3, yay=True)], _sender=signer1
            )
            sc.verify(multisignAdmin.data.quorum == 3)
            now = now.add_seconds(1)

            ##########
            # Cancel #
            ##########
            sc.h2("Proposal cancellation")
            sc.h3("New proposal")
            sc.verify(multisignAdmin.data.timeout != 10)
            changeTimeout = SelfHelper.changeTimeout(10)
            multisignAdmin.newProposal([changeTimeout], _sender=signer1, _now=now)
            sc.h3("Signer 2 tries to cancel the proposal")
            voterId = multisignAdmin.data.addrVoterId[signer1.address]
            proposalId = multisignAdmin.data.proposals[voterId].id
            multisignAdmin.cancelProposal(proposalId, _sender=signer2, _valid=False)
            sc.h3("Signer 1 cancels the proposal")
            multisignAdmin.cancelProposal(proposalId, _sender=signer1)
            sc.h3("Signer 2 tries to vote the canceled proposal")
            multisignAdmin.vote(
                [vote(multisignAdmin, signer1, yay=True)],
                _sender=signer2,
                _valid=False,
            )
            sc.verify(multisignAdmin.data.timeout != 10)

            ############
            # Rejected #
            ############
            sc.h2("Proposal rejection")
            sc.h3("New proposal")
            sc.verify(multisignAdmin.data.timeout != 10)
            changeTimeout = SelfHelper.changeTimeout(10)
            multisignAdmin.newProposal([changeTimeout], _sender=signer1, _now=now)
            sc.h3("Signer 2 votes against the proposal")
            multisignAdmin.vote(
                [vote(multisignAdmin, signer1, yay=False)], _sender=signer2
            )
            sc.h3("Signer 3 votes against the proposal")
            sc.verify(multisignAdmin.data.proposals[voterId].canceled == False)
            multisignAdmin.vote(
                [vote(multisignAdmin, signer1, yay=False)], _sender=signer3
            )
            voterId = multisignAdmin.data.addrVoterId[signer1.address]
            sc.verify(multisignAdmin.data.proposals[voterId].canceled == True)
            sc.verify(multisignAdmin.data.timeout != 10)

            ######################
            # Remove signer fail #
            ######################
            sc.h2("Invalid Removed signer proposal")
            sc.h3("Signer 1 new proposal: remove signer 3")
            changeVoters = SelfHelper.changeVoters(removed=[signer3.address])
            multisignAdmin.newProposal([changeVoters], _sender=signer1, _now=now)
            sc.h3("Signer 2 votes the remove proposal")
            multisignAdmin.vote(
                [vote(multisignAdmin, signer1, yay=True)], _sender=signer2
            )
            sc.h3("Signer 3 tries to vote the remove proposal")
            sc.p("Fails because quorum would be > number of signers")
            multisignAdmin.vote(
                [vote(multisignAdmin, signer1, yay=True)],
                _sender=signer3,
                _valid=False,
            )
            sc.verify(multisignAdmin.data.voters.contains(2))

            ######################
            # 2 actions proposal #
            ######################
            sc.h2("2 actions proposal")
            sc.h3("Signer 1 new proposal: change quorum to 2 and remove signer 3")
            sc.verify(multisignAdmin.data.quorum == 3)
            sc.verify(multisignAdmin.data.voters.contains(2))
            changeQuorum = SelfHelper.changeQuorum(2)
            changeVoters = SelfHelper.changeVoters(removed=[signer3.address])
            multisignAdmin.newProposal(
                [changeQuorum, changeVoters], _sender=signer1, _now=now
            )
            sc.h3("Signer 2 votes the proposal")
            multisignAdmin.vote(
                [vote(multisignAdmin, signer1, yay=True)], _sender=signer2
            )
            sc.h3("Signer 3 votes the proposal")
            multisignAdmin.vote(
                [vote(multisignAdmin, signer1, yay=True)], _sender=signer3
            )
            now = now.add_seconds(1)
            sc.verify(multisignAdmin.data.quorum == 2)
            sc.verify(~multisignAdmin.data.voters.contains(2))

            ###########################
            # Votes for past proposal #
            ###########################
            sc.h2("Vote for past proposal")
            sc.h3("Signer 1 new proposal: change timeout to 2")
            changeTimeout = SelfHelper.changeTimeout(2)
            multisignAdmin.newProposal([changeTimeout], _sender=signer1, _now=now)
            sc.h3("Signer 2 new proposal: add new signer")
            sc.verify(multisignAdmin.data.timeout != 3)
            changeVoters = SelfHelper.changeVoters(
                [], added=[(signer4.address, signer4.public_key)]
            )
            multisignAdmin.newProposal([changeVoters], _sender=signer2)
            now = now.add_seconds(1)
            sc.h3("Signer 2 tries to vote signer1's proposal after timedout")
            multisignAdmin.vote(
                [vote(multisignAdmin, signer1, yay=True)],
                _sender=signer2,
                _now=now.add_minutes(100),
                _valid=False,
            )
            sc.h3("Signer 1 votes for signer2's proposal")
            multisignAdmin.vote(
                [vote(multisignAdmin, signer2, yay=True)], _sender=signer1, _now=now
            )
            sc.h3(
                "Signer 2 tries to vote signer1's proposal while a more recent one was accepted"
            )
            multisignAdmin.vote(
                [vote(multisignAdmin, signer1, yay=True)],
                _sender=signer2,
                _now=now.add_seconds(1),
                _valid=False,
            )
            now = now.add_seconds(1)

            ##############
            # Multivotes #
            ##############
            sc.h2("Multi vote in one call")
            sc.h3("Signer 1 new proposal")
            changeTimeout = SelfHelper.changeTimeout(2)
            multisignAdmin.newProposal([changeTimeout], _sender=signer1, _now=now)
            now = now.add_seconds(1)
            sc.h3("Signer 2 and Signer 3 votes are pushed by Signer 1")
            signer2_vote = sign(
                signer2,
                voterId=1,
                contract=multisignAdmin,
                initiatorId=0,
                proposalId=proposalId,
                yay=True,
            )
            signer4_vote = sign(
                signer4,
                voterId=3,
                contract=multisignAdmin,
                initiatorId=0,
                proposalId=proposalId,
                yay=True,
            )
            proposalVotes = sp.record(
                initiatorId=0,
                proposalId=proposalId,
                votes=[signer2_vote, signer4_vote],
            )
            multisignAdmin.multiVote([proposalVotes], _sender=signer1, _now=now)
            sc.verify(multisignAdmin.data.timeout == 2)
            now = now.add_seconds(1)

        ##########################################

        else:
            #########################
            # Target Administration #
            #########################
            now = sp.timestamp(2)
            sc.h2("Set multisignAdmin as administrated's admin")
            administrated.administrate(
                [sp.variant.changeAdmin(multisignAdmin.address)],
                _sender=admin,
                _now=now,
            )

            sc.h2("Use multisignadmin to set a target")
            sc.h3("Signer 1 new proposal: changeTarget")
            now = now.add_seconds(10)
            targetAddress = sp.contract(
                sp.list[m2.t_targetAdminAction],
                administrated.address,
                entrypoint="administrate",
            ).unwrap_some()
            multisignAdmin.newProposal(
                [SelfHelper.changeTarget(sp.to_address(targetAddress))],
                _sender=signer1,
                _now=now,
            )

            sc.h2("Use multisignadmin to administrate target")
            sc.h3("Signer 1 new proposal: changeActive = True on target")
            sc.verify(~administrated.data.active)
            now = now.add_seconds(12)
            changeTargetActive = sp.variant(
                "targetAdmin", [sp.variant.changeActive(True)]
            )
            multisignAdmin.newProposal([changeTargetActive], _sender=signer1, _now=now)
            sc.verify(administrated.data.active)


if "main" in __name__:
    add_test("Self Administration tests")
    add_test("Target Administration tests")
