import smartpy as sp
from smartpy.templates import fa2_lib as FA2
from smartpy.templates import price_feed_multisign_admin as MSA

main = FA2.main


@sp.module
def m():
    import main

    # Constants

    NAME = "Price Feed Aggregator"
    DESCRIPTION = "XTZ/EUR"
    VERSION = "1"
    RESERVE_ROUNDS = 2
    LINK_TOKEN_ID = 0
    DECIMALS = sp.nat(8)
    TIMEOUT = sp.nat(10)  # In minutes
    ORACLE_PAYMENT = sp.nat(1)
    MAX_ROUND = 4294967295  # 2**32-1
    USE_BIGMAP_ORACLES = False

    # TODO: activate when metadata is implemented
    # AGGREGATOR_METADATA = {
    #     "name"          : NAME,
    #     "version"       : VERSION,
    #     "description"   : DESCRIPTION,
    #     "source"        : {
    #         "tools": [ "SmartPy" ]
    #     },
    #     "interfaces"    : [ "TZIP-016" ],
    # }

    # Types

    # Round specification type
    t_roundData: type = sp.record(
        roundId=sp.nat,
        answer=sp.nat,
        startedAt=sp.timestamp,
        updatedAt=sp.timestamp,
        answeredInRound=sp.nat,
    )
    # Round details specification type
    t_roundDetails: type = sp.record(
        submissions=sp.map[sp.address, sp.nat],
        minSubmissions=sp.nat,
        maxSubmissions=sp.nat,
        timeout=sp.nat,
        activeOracles=sp.set[sp.address],
    )
    # Oracle details specification type
    t_oracleDetails: type = sp.record(
        startingRound=sp.nat,
        endingRound=sp.nat,
        lastStartedRound=sp.nat,
        withdrawable=sp.nat,
        adminAddress=sp.address,
    )
    # Link token recorded funds specification type
    t_recordedFunds: type = sp.record(available=sp.nat, allocated=sp.nat)
    # Proxy Admin Action specification type
    t_proxyAdminAction: type = sp.variant(
        changeActive=sp.bool, changeAdmin=sp.address, changeAggregator=sp.address
    )
    # Aggregator Admin Action specification type
    t_aggregatorAdminAction: type = sp.variant(
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

    t_storage_type: type = sp.record(
        active=sp.bool,
        decimals=sp.nat,
        admin=sp.address,
        metadata=sp.big_map[sp.string, sp.bytes],
        minSubmissions=sp.nat,
        maxSubmissions=sp.nat,
        restartDelay=sp.nat,
        timeout=sp.nat,  # In minutes
        oraclePayment=sp.nat,
        latestRoundId=sp.nat,
        reportingRoundId=sp.nat,
        rounds=sp.big_map[sp.nat, t_roundData],
        previousRoundDetails=t_roundDetails,
        reportingRoundDetails=t_roundDetails,
        linkToken=sp.address,
        recordedFunds=t_recordedFunds,
        oraclesAddresses=sp.set[sp.address],
        oracles=sp.big_map[sp.address, t_oracleDetails],
    )

    t_fa2_balance_of_request: type = sp.record(
        owner=sp.address, token_id=sp.nat
    ).layout(("owner", "token_id"))

    t_fa2_balance_of_response: type = sp.record(
        request=t_fa2_balance_of_request, balance=sp.nat
    ).layout(("request", "balance"))

    t_fa2_balance_of_params: type = sp.record(
        callback=sp.contract[list[t_fa2_balance_of_response]],
        requests=list[t_fa2_balance_of_request],
    ).layout(("requests", "callback"))

    t_fa2_tx: type = sp.record(
        to_=sp.address,
        token_id=sp.nat,
        amount=sp.nat,
    ).layout(("to_", ("token_id", "amount")))

    t_fa2_transfer_batch: type = sp.record(
        from_=sp.address,
        txs=list[t_fa2_tx],
    ).layout(("from_", "txs"))

    t_fa2_transfer_params: type = list[t_fa2_transfer_batch]

    Aggregator_NotAdmin = "Aggregator_NotAdmin"
    Aggregator_NotOracle = "Aggregator_NotOracle"
    Aggregator_NotYetEnabledOracle = "Aggregator_NotYetEnabledOracle"
    Aggregator_NotLongerAllowedOracle = "Aggregator_NotLongerAllowedOracle"
    Aggregator_InvalidRound = "Aggregator_InvalidRound"
    Aggregator_FutureRound = "Aggregator_FutureRound"
    Aggregator_RoundNotOver = "Aggregator_RoundNotOver"
    Aggregator_PreviousRoundNotOver = "Aggregator_PreviousRoundNotOver"
    Aggregator_WaitBeforeInit = "Aggregator_WaitBeforeInit"
    Aggregator_AlreadySubmitted = "Aggregator_AlreadySubmittedForThisRound"
    Aggregator_SubmittedInCurrent = "Aggregator_SubmittedInCurrent"
    Aggregator_CurrentHasValue = "Aggregator_CurrentHasValue"
    Aggregator_CallbackNotFound = "Aggregator_CallbackNotFound"
    Aggregator_DelayExceedTotal = "Aggregator_DelayExceedTotal"
    Aggregator_MaxSubmissions = "Aggregator_RoundMaxSubmissionExceed"
    Aggregator_MaxInferiorToMin = "Aggregator_MaxInferiorToMin"
    Aggregator_MaxExceedActive = "Aggregator_MaxExceedActive"
    Aggregator_OraclePaymentUnderflow = "Aggregator_OraclePaymentUnderflow"
    Aggregator_NotOracleAdmin = "Aggregator_NotOracleAdmin"
    Aggregator_InsufficientWithdrawableFunds = (
        "Aggregator_InsufficientWithdrawableFunds"
    )
    Aggregator_NotLinkToken = "Aggregator_NotLinkToken"
    Aggregator_InvalidTokenInterface = "Aggregator_InvalidTokenkInterface"
    Aggregator_MinSubmissionsTooLow = "Aggregator_MinSubmissionsTooLow"
    Aggregator_InsufficientFundsForPayment = "Aggregator_InsufficientFundsForPayment"

    Proxy_InvalidParametersInLatestRoundDataView = (
        "Proxy_InvalidParametersInLatestRoundDataView"
    )
    Proxy_InvalidParametersInDecimalsView = "Proxy_InvalidParametersInDecimalsView"
    Proxy_InvalidParametersInDescriptionView = (
        "Proxy_InvalidParametersInDescriptionView"
    )
    Proxy_InvalidParametersInVersionView = "Proxy_InvalidParametersInVersionView"
    Proxy_AggregatorNotConfigured = "Proxy_AggregatorNotConfigured"
    Proxy_NotAdmin = "Proxy_NotAdmin"

    def median(submissions):
        """Returns the sorted middle, or the average of the two middle indexed items if the array has an even number of elements."""
        xs = submissions
        result = 0
        half = sp.len(xs) / 2
        hist = {}
        average = not (half * 2 != sp.len(xs))
        for x in xs:
            if hist.contains(x):
                hist[x] += 1
            else:
                hist[x] = 1
        i = 0
        for x in hist.items():
            if average:
                if i < half:
                    result = x.key
                else:
                    result += x.key
                    result /= 2
                    average = False
                i += x.value
            else:
                if i <= half:
                    result = x.key
                    i += x.value
        return result

    class PriceAggregator(sp.Contract):
        def __init__(
            self,
            initialRoundDetails,
            tokenAddress,
            active,
            decimals,
            admin,
            oracles,
            timeout,
            oraclePayment,
            minSubmissions,
            maxSubmissions,
            restartDelay,
            metadata,
        ):
            """
            This contract aggregates off-chain data pushed by oracles.

            The submissions are gathered in rounds, with each round aggregating the submissions
            for each oracle into a single answer.

            The latest aggregated answer is exposed as well as historical answers and their updated at timestamp.

            Args:
                useBigmapOracles           : Use a big map to store the oracles
                initialRoundDetails        : Initial round details
                tokenContract (sp.Contract): Token Contract used for payment
                tokenAddress (sp.address) : Address of the token used for payments
                active (sp.bool)          : Aggregator state
                decimals (sp.nat)         : The number of decimals in the answer.
                admin (sp.address)        : Admin address, supposely the PriceAggregatorAdmin multisign contract
                oracleDetails (TYPES.TOracleDetails) : Parameters of the Oracle
                timeout (sp.nat)          : Number of minutes after which a new round can be initiate
                oraclePayment (sp.nat)    : Amount of Token payed to Oracle at each Submission
                minSubmissions (sp.nat)   : Min submissions' number to be able to update a value
                maxSubmissions (sp.nat)   : Max submissions' number to be able to seal a value
                restartDelay (sp.nat)     : Number of rounds an Oracle has to wait between 2 round initiate
                metadata(sp.big_map of str bytes) : metadata bigmap
            """

            # TODO: activate when metadata is implemented
            # # Generate the metadata representation
            # # The generated metadata should be copied and destributed with IPFS
            # self.init_metadata("metadata", {
            #     **AGGREGATOR_METADATA,
            #     "views" : [
            #         self.getDecimals,
            #         self.getWithdrawablePayment,
            #         self.getRoundData
            #     ],
            # })

            sp.cast(self.data, t_storage_type)

            self.data.active = active
            self.data.decimals = decimals
            self.data.admin = admin
            self.data.metadata = metadata

            self.data.minSubmissions = minSubmissions
            self.data.maxSubmissions = maxSubmissions
            self.data.restartDelay = restartDelay
            self.data.timeout = timeout
            self.data.oraclePayment = oraclePayment

            self.data.latestRoundId = 0
            self.data.reportingRoundId = 0

            self.data.rounds = sp.big_map()
            self.data.previousRoundDetails = initialRoundDetails
            self.data.reportingRoundDetails = initialRoundDetails

            self.data.linkToken = tokenAddress
            self.data.recordedFunds = sp.record(available=0, allocated=0)

            self.data.oracles = sp.big_map()
            self.data.oraclesAddresses = set()

            for oracle in oracles.items():
                self.data.oracles[oracle.key] = oracle.value
                self.data.oraclesAddresses.add(oracle.key)

        @sp.private(with_storage="read-write")
        def updatePrevious(self, submission):
            currentRoundId = self.data.reportingRoundId
            previousRoundId = sp.as_nat(currentRoundId - 1)
            previousRoundDetails = self.data.previousRoundDetails

            assert not previousRoundDetails.submissions.contains(
                sp.sender
            ), Aggregator_SubmittedInCurrent
            assert (
                sp.len(previousRoundDetails.submissions)
                < previousRoundDetails.maxSubmissions
            ), Aggregator_MaxSubmissions

            previousRoundDetails.submissions[sp.sender] = submission
            if (
                sp.len(previousRoundDetails.submissions)
                >= previousRoundDetails.minSubmissions
            ):
                self.data.rounds[previousRoundId].answer = median(
                    previousRoundDetails.submissions.values()
                )
                self.data.rounds[previousRoundId].updatedAt = sp.now
                self.data.rounds[previousRoundId].answeredInRound = currentRoundId
            self.data.previousRoundDetails = previousRoundDetails

        @sp.private(with_storage="read-write")
        def updateCurrent(self, submission):
            currentRoundId = self.data.reportingRoundId
            currentRoundDetails = self.data.reportingRoundDetails

            assert not currentRoundDetails.submissions.contains(
                sp.sender
            ), Aggregator_AlreadySubmitted
            assert (
                sp.len(currentRoundDetails.submissions)
                < currentRoundDetails.maxSubmissions
            ), Aggregator_MaxSubmissions

            currentRoundDetails.submissions[sp.sender] = submission
            if (
                sp.len(currentRoundDetails.submissions)
                >= currentRoundDetails.minSubmissions
            ):
                self.data.rounds[currentRoundId].answer = median(
                    currentRoundDetails.submissions.values()
                )
                self.data.rounds[currentRoundId].updatedAt = sp.now
                self.data.rounds[currentRoundId].answeredInRound = currentRoundId
                self.data.latestRoundId = currentRoundId
            self.data.reportingRoundDetails = currentRoundDetails

        @sp.private(with_storage="read-write")
        def updateNext(self, submission):
            currentRoundId = self.data.reportingRoundId
            nextRoundId = currentRoundId + 1

            if currentRoundId > 0:
                currentRound = self.data.rounds[currentRoundId]

                timeout = sp.add_seconds(
                    currentRound.startedAt, sp.to_int(self.data.timeout) * 60
                )
                roundInit_delay = (
                    self.data.oracles[sp.sender].lastStartedRound
                    + self.data.restartDelay
                )

                assert (self.data.oracles[sp.sender].lastStartedRound == 0) or (
                    nextRoundId > roundInit_delay
                ), Aggregator_WaitBeforeInit
                assert (sp.now > timeout) or (
                    currentRound.answeredInRound == currentRoundId
                ), Aggregator_PreviousRoundNotOver

            # If minimum submissions is 1, then include the answer in the round initialization
            answer = 0
            answeredInRound = 0
            if self.data.minSubmissions == 1:
                answer = submission
                answeredInRound = nextRoundId

            self.data.rounds[nextRoundId] = sp.record(
                roundId=nextRoundId,
                answer=answer,
                startedAt=sp.now,
                updatedAt=sp.now,
                answeredInRound=answeredInRound,
            )

            self.data.previousRoundDetails = self.data.reportingRoundDetails

            activeOracles = set()
            for oracle in self.data.oraclesAddresses.elements():
                oracleDetails = self.data.oracles[oracle]
                if (oracleDetails.endingRound >= nextRoundId) and (
                    oracleDetails.startingRound <= nextRoundId
                ):
                    activeOracles.add(oracle)

            self.data.reportingRoundDetails = sp.record(
                submissions={sp.sender: submission},
                minSubmissions=self.data.minSubmissions,
                maxSubmissions=self.data.maxSubmissions,
                timeout=self.data.timeout,
                activeOracles=activeOracles,
            )

            self.data.oracles[sp.sender].lastStartedRound = nextRoundId
            self.data.reportingRoundId = nextRoundId

        @sp.entrypoint
        def submit(self, params):
            """
            Called by oracles when they have witnessed a need to update

            Args:
                roundId (sp.Nat)     : ID of the round this submission pertains to
                submission (sp.nat) : updated data that the oracle is submitting
            """
            currentRoundId = self.data.reportingRoundId
            (roundId, submission) = params

            assert self.data.active
            assert self.data.oracles.contains(sp.sender), Aggregator_NotOracle
            assert (
                self.data.oracles[sp.sender].startingRound <= roundId
            ), Aggregator_NotYetEnabledOracle
            assert (
                self.data.oracles[sp.sender].endingRound > roundId
            ), Aggregator_NotLongerAllowedOracle

            # Only allow new submissions in [currentRoundId -1; currentRoundId +1] round interval
            assert (
                (roundId + 1 == currentRoundId)
                or (roundId == currentRoundId)
                or (roundId == currentRoundId + 1)
            ), Aggregator_InvalidRound

            if (roundId + 1) == currentRoundId:
                _ = self.updatePrevious(submission)
            else:
                if roundId == currentRoundId:
                    _ = self.updateCurrent(submission)
                else:
                    _ = self.updateNext(submission)

            # Update the oracle withdrawable amount
            _ = self.payOracle(sp.sender)

        @sp.entrypoint
        def administrate(self, actions):
            assert sp.sender == self.data.admin, Aggregator_NotAdmin
            sp.cast(actions, sp.list[t_aggregatorAdminAction])
            for action in actions:
                match action:
                    case changeActive(active):
                        self.data.active = active
                    case changeAdmin(admin):
                        self.data.admin = admin
                    case updateFutureRounds(futureRounds):
                        _ = self.updateFutureRounds(futureRounds)
                    case changeOracles(params):
                        _ = self.changeOracles(params)

        @sp.private(with_storage="read-write")
        def updateFutureRounds(self, params):
            assert sp.sender == self.data.admin, Aggregator_NotAdmin

            oraclesCount = sp.len(self.data.oraclesAddresses)
            assert (
                params.maxSubmissions >= params.minSubmissions
            ), Aggregator_MaxInferiorToMin
            assert oraclesCount >= params.maxSubmissions, Aggregator_MaxExceedActive
            assert (oraclesCount == 0) or (
                oraclesCount > params.restartDelay
            ), Aggregator_DelayExceedTotal
            assert (oraclesCount == 0) or (
                params.minSubmissions > 0
            ), Aggregator_MinSubmissionsTooLow

            required_funds = params.oraclePayment * oraclesCount * RESERVE_ROUNDS
            assert (
                self.data.recordedFunds.available >= required_funds
            ), Aggregator_InsufficientFundsForPayment

            self.data.restartDelay = params.restartDelay
            self.data.minSubmissions = params.minSubmissions
            self.data.maxSubmissions = params.maxSubmissions
            self.data.timeout = params.timeout
            self.data.oraclePayment = params.oraclePayment

        @sp.private(with_storage="read-write")
        def changeOracles(self, params):
            assert sp.sender == self.data.admin, Aggregator_NotAdmin
            for oracleAddress in params.removed:
                del self.data.oracles[oracleAddress]
                self.data.oraclesAddresses.remove(oracleAddress)

            for oracle in params.added:
                (oracleAddress, oracleData) = oracle
                endingRound = MAX_ROUND

                if oracleData.endingRound.is_some():
                    endingRound = oracleData.endingRound.unwrap_some()

                self.data.oracles[oracleAddress] = sp.record(
                    startingRound=oracleData.startingRound,
                    endingRound=endingRound,
                    adminAddress=oracleData.adminAddress,
                    lastStartedRound=0,
                    withdrawable=sp.nat(0),
                )

                self.data.oraclesAddresses.add(oracleAddress)

                reportingRoundId = self.data.reportingRoundId
                if (reportingRoundId != 0) and (
                    oracleData.startingRound <= reportingRoundId
                ):
                    self.data.reportingRoundDetails.activeOracles.add(oracleAddress)

        @sp.entrypoint
        def decimals(self, callback):
            """Returns the number of decimals in the answer (e.g. 8)"""
            sp.transfer(self.data.decimals, sp.tez(0), callback)

        @sp.entrypoint
        def latestRoundData(self, callback):
            """
            Callback with data about the latest round. Consumers are encouraged
            to check that they're receiving fresh data by inspecting the
            updatedAt and answeredInRound return values.

            Args:
                callback : sp.address

            Returns:
                roundId (sp.nat): round ID for which data was retrieved
                answer (sp.nat):  the answer for the given round
                startedAt (sp.timestamp): timestamp when the round was started.
                updatedAt (sp.timestamp): timestamp when the answer was updated.
                    (i.e. answer was last computed)
                answeredInRound (sp.nat): the round ID of the round in which
                    the answer was computed. answeredInRound may be smaller than
                    roundId when the round timed out.
                    answeredInRound is equal to roundId when the round didn't
                    time out and was computed regularly.

                Note that for in-progress rounds (i.e. rounds that haven't yet
                received maxSubmissions) answer and updatedAt may change
                between queries.
            """
            sp.transfer(self.data.rounds[self.data.latestRoundId], sp.tez(0), callback)

        @sp.offchain_view
        def getWithdrawablePayment(self, oracleAddress):
            """
            Gets the available amount that an oracle can withdraw

            Args:
                oracleAddress : sp.address

            Returns:
                sp.nat : Withdrawable payment amount
            """
            return self.data.oracles[oracleAddress].withdrawable

        @sp.offchain_view
        def getDecimals(self):
            """
            Gets the number of decimals in the answer (e.g. 8)

            Returns:
                sp.nat : the number of decimals
            """
            return self.data.decimals

        @sp.offchain_view
        def getRoundData(self, roundId):
            """
            Gets the information of a specific round

            Args:
                roundId : sp.nat

            Returns:
                roundId         (sp.nat)       : round ID for which data was retrieved.
                answer          (sp.nat)       : the answer for the given round.
                startedAt       (sp.timestamp) : timestamp when the round was started.
                updatedAt       (sp.timestamp) : timestamp when the answer was updated.
                answeredInRound (sp.nat)       : the round ID of the round in which
                    the answer was computed. answeredInRound may be smaller than
                    roundId when the round timed out.
                    answeredInRound is equal to roundId when the round didn't
                    time out and was computed regularly.

                Note that for in-progress rounds (i.e. rounds that haven't yet
                received maxSubmissions) answer and updatedAt may change
                between queries.
            """
            if self.data.rounds.contains(roundId):
                return sp.Some(self.data.rounds[roundId])
            else:
                return None

        @sp.private(with_storage="read-write")
        def payOracle(self, oracle):
            """
            Update the withdrawable amount of a specific oracle after a sucessul submission
            """
            payment = self.data.oraclePayment
            funds = self.data.recordedFunds
            funds.available = sp.as_nat(
                funds.available - payment, error=Aggregator_OraclePaymentUnderflow
            )
            funds.allocated += payment
            self.data.recordedFunds = funds
            self.data.oracles[oracle].withdrawable += payment

        @sp.private(with_storage="read-write", with_operations=True)
        def requestBalanceUpdate(self, updateAvailableFunds):
            """
            Call Link token and request a balance update

            Args:
                updateAvailableFunds (sp.contract): updateAvailableFunds's entrypoint
            """
            contract = sp.contract(
                t_fa2_balance_of_params, self.data.linkToken, entrypoint="balance_of"
            ).unwrap_some(error=Aggregator_InvalidTokenInterface)

            args = sp.record(
                callback=updateAvailableFunds,
                requests=[sp.record(owner=sp.self_address, token_id=LINK_TOKEN_ID)],
            )
            sp.transfer(args, sp.tez(0), contract)

        @sp.entrypoint
        def forceBalanceUpdate(self):
            """
            Call Link token and request a balance update (Forced, this should be called after an origination)
            """
            _ = self.requestBalanceUpdate(sp.self_entrypoint("updateAvailableFunds"))

        @sp.entrypoint
        def updateAvailableFunds(self, params):
            """
            Receive balance update from link token
            """
            sp.cast(params, sp.list[t_fa2_balance_of_response])

            # Ensure that this entrypoint is only called by the configured token
            assert sp.sender == self.data.linkToken, Aggregator_NotLinkToken

            balance = 0
            for resp in params:
                assert resp.request.owner == sp.self_address
                balance = resp.balance

            if balance != self.data.recordedFunds.available:
                self.data.recordedFunds.available = balance

        @sp.entrypoint
        def withdrawPayment(self, params):
            """
            Transfers the oracle's LINK to another address. Can only be called by the oracle's admin.

            Args:
                oracleAddress       : sp.address   is the oracle whose LINK is transferred
                recipientAddress    : sp.address   is the address to send the LINK to
                amount              : sp.nat       is the amount of LINK to send
            """
            assert (
                self.data.oracles[params.oracleAddress].adminAddress == sp.sender
            ), Aggregator_NotOracleAdmin

            withdrawable = self.data.oracles[params.oracleAddress].withdrawable

            assert (
                withdrawable >= params.amount
            ), Aggregator_InsufficientWithdrawableFunds

            self.data.oracles[params.oracleAddress].withdrawable = sp.as_nat(
                withdrawable - params.amount
            )
            self.data.recordedFunds.allocated = sp.as_nat(
                self.data.recordedFunds.allocated - params.amount
            )

            token = sp.contract(
                t_fa2_transfer_params, self.data.linkToken, entrypoint="transfer"
            ).unwrap_some(error=Aggregator_InvalidTokenInterface)
            arg = [
                sp.record(
                    from_=sp.self_address,
                    txs=[
                        sp.record(
                            to_=params.recipientAddress,
                            token_id=LINK_TOKEN_ID,
                            amount=params.amount,
                        )
                    ],
                )
            ]
            # Send payment
            sp.transfer(arg, sp.tez(0), token)
            # Resync available funds
            _ = self.requestBalanceUpdate(sp.self_entrypoint("updateAvailableFunds"))

    class Proxy(sp.Contract):
        def __init__(self, active, admin, aggregator):
            sp.cast(
                self.data,
                sp.record(
                    active=sp.bool, admin=sp.address, aggregator=sp.option[sp.address]
                ),
            )

            self.data.active = active
            self.data.admin = admin
            self.data.aggregator = aggregator

        @sp.entrypoint
        def decimals(self, params):
            aggregator = self.data.aggregator.unwrap_some(
                error=Proxy_AggregatorNotConfigured
            )
            view = sp.contract(
                sp.pair[sp.unit, sp.address], aggregator, entrypoint="decimals"
            ).unwrap_some(error=Proxy_InvalidParametersInDecimalsView)

            sp.transfer(params, sp.tez(0), view)

        @sp.entrypoint
        def version(self, params):
            aggregator = self.data.aggregator.unwrap_some(
                error=Proxy_AggregatorNotConfigured
            )
            view = sp.contract(
                sp.pair[sp.unit, sp.address], aggregator, entrypoint="version"
            ).unwrap_some(error=Proxy_InvalidParametersInVersionView)

            sp.transfer(params, sp.tez(0), view)

        @sp.entrypoint
        def description(self, params):
            aggregator = self.data.aggregator.unwrap_some(
                error=Proxy_AggregatorNotConfigured
            )
            view = sp.contract(
                sp.pair[sp.unit, sp.address], aggregator, entrypoint="description"
            ).unwrap_some(error=Proxy_InvalidParametersInDescriptionView)
            sp.transfer(params, sp.tez(0), view)

        @sp.entrypoint
        def latestRoundData(self, params):
            aggregator = self.data.aggregator.unwrap_some(
                error=Proxy_AggregatorNotConfigured
            )
            view = sp.contract(
                sp.pair[sp.unit, sp.address], aggregator, "latestRoundData"
            ).unwrap_some(error=Proxy_InvalidParametersInLatestRoundDataView)
            sp.transfer(params, sp.tez(0), view)

        @sp.entrypoint
        def administrate(self, actions):
            assert sp.sender == self.data.admin, Proxy_NotAdmin
            sp.cast(actions, sp.list[t_proxyAdminAction])
            for action in actions:
                match action:
                    case changeActive(active):
                        self.data.active = active
                    case changeAdmin(admin):
                        self.data.admin = admin
                    case changeAggregator(aggregator):
                        self.data.aggregator = sp.Some(aggregator)

    class Viewer(sp.Contract):
        def __init__(self, admin, proxy):
            self.data.admin = admin
            self.data.proxy = proxy
            self.data.latestRoundData = None

        @sp.entrypoint
        def getLatestRoundData(self):
            proxy = sp.contract(
                sp.address, self.data.proxy, entrypoint="latestRoundData"
            ).unwrap_some(
                error="Wrong Interface: Could not resolve proxy latestRoundData entrypoint."
            )

            sp.transfer(
                sp.to_address(sp.self_entrypoint("setLatestRoundData")),
                sp.tez(0),
                proxy,
            )

        @sp.entrypoint
        def setLatestRoundData(self, latestRoundData):
            sp.cast(latestRoundData, t_roundData)
            assert sp.sender == self.data.proxy
            self.data.latestRoundData = sp.Some(latestRoundData)

        @sp.entrypoint
        def setup(self, admin, proxy):
            assert sp.sender == self.data.admin
            self.data.admin = admin
            self.data.proxy = proxy

    # Order of inheritance: [Admin], [<policy>], <base class>, [<mixins>]

    class LinkToken(
        main.Admin,
        main.PauseOwnerOrOperatorTransfer,
        main.SingleAsset,
        main.ChangeMetadata,
        main.WithdrawMutez,
        main.MintSingleAsset,
        main.BurnSingleAsset,
        main.OffchainviewTokenMetadata,
        main.OnchainviewBalanceOf,
    ):
        def __init__(self, administrator, metadata, ledger, token_metadata):
            main.OnchainviewBalanceOf.__init__(self)
            main.OffchainviewTokenMetadata.__init__(self)
            main.BurnSingleAsset.__init__(self)
            main.MintSingleAsset.__init__(self)
            main.WithdrawMutez.__init__(self)
            main.ChangeMetadata.__init__(self)
            main.SingleAsset.__init__(self, metadata, ledger, token_metadata)
            main.PauseOwnerOrOperatorTransfer.__init__(self)
            main.Admin.__init__(self, administrator)


# CONSTANTS (Useful when originating the contracts)
GENERATE_DEPLOYMENT_CONTRACTS = False

ADMIN_ADDRESS = sp.address("tz1evBmfWZoPDN38avoRGbjJaLBJUP8AZz6a")
AGGREGATOR_ADDRESS = sp.address("KT1CfuSjCcunNQ5qCCro2Kc74uivnor9d8ba")
PROXY_ADDRESS = sp.address("KT1PG6uK91ymZYVtjnRXv2mEdFYSH6P6uJhC")
TOKEN_ADDRESS = sp.address("KT1LcrXERzpDeUXWxLEWnLipHrhWEhzSRTt7")

ORACLE_1_ADDRESS = sp.address("KT1LhTzYhdhxTqKu7ByJz8KaShF6qPTdx5os")
ORACLE_2_ADDRESS = sp.address("KT1P7oeoKWHx5SXt73qpEanzkr8yeEKABqko")
ORACLE_3_ADDRESS = sp.address("KT1SCkxmTqTkmc7zoAP5uMYT9rp9iqVVRgdt")
ORACLE_4_ADDRESS = sp.address("KT1LLTzYhdhxTqKu7ByJz8KaShF6qPTdx5os")
ORACLE_5_ADDRESS = sp.address("KT1P6oeoKWHx5SXt73qpEanzkr8yeEKABqko")
ORACLE_6_ADDRESS = sp.address("KT1SskxmTqTkmc7zoAP5uMYT9rp9iqVVRgdt")

# Admins/Signers of multisign admin contract
ACCOUNT_1_ADDRESS = sp.address("tz1evBmfWZoPDN38avoRGbjJaLBJUP8AZz6a")
ACCOUNT_1_PUBLIC_KEY = sp.key("edpkuZ7ERiU5B8knLqQsVMH86j9RLMUyHyL665oCXDkPQxF7HGqSeJ")
ACCOUNT_1_SECRET = "edskRowES25ZTKFDV5GJamCUfLB1gjE9YP25kfXtxNg8WTMiFuoD5gtUa3Evk3gViFADogBeDhWBjHNDJoQ44sWzQzaoTH4qcj"
ACCOUNT_2_ADDRESS = sp.address("tz1NDUP7uyQNFsSzamkPMfbxirMrg3D6TR2w")
ACCOUNT_2_PUBLIC_KEY = sp.key("edpktwD9RYpBiqhFCsaN3t7BbF7uT3zqRfkSWCwuDdfMUDMwDnk9Tz")
ACCOUNT_2_SECRET = "edskS4dHu2VNf8eyLhqoMRUtzWdcTMd4y8qJVe19ea5P2N2D1M4Puizfbh9zoRpHAASPYtMcSRbrVFC127EY11nDJPEH62cYKR"

################
# + Test Helpers
################


def compute_latest_data(sc, aggregator):
    data = aggregator.data.rounds[aggregator.data.latestRoundId]
    return sc.compute(data)


def add_oracle(oracle, startingRound, endingRound, lastStartedRound):
    return sp.pair(
        oracle,
        sp.record(
            startingRound=startingRound,
            endingRound=sp.Some(endingRound),
            lastStartedRound=lastStartedRound,
        ),
    )


################
# - Test Helpers
################

###################################
# Multisign Administrator Helpers #
###################################


class MSAggregatorHelper:
    def variant(content):
        return sp.variant.targetAdmin(content)

    def changeAdmin(admin):
        return sp.variant.changeAdmin(admin)

    def changeActive(active):
        return sp.variant.changeActive(active)

    def changeOracles(removed=[], added=[]):
        return sp.variant(
            "changeOracles", sp.record(removed=sp.list(removed), added=sp.list(added))
        )

    def oracle(address, admin, startingRound, endingRound=None):
        oracle_pair = sp.pair(
            address,
            sp.record(
                startingRound=startingRound, endingRound=endingRound, adminAddress=admin
            ),
        )
        sp.set_type_expr(
            oracle_pair,
            sp.pair[
                sp.address,
                sp.record(
                    startingRound=sp.nat,
                    endingRound=sp.option[sp.nat],
                    adminAddress=sp.address,
                ),
            ],
        )
        return oracle_pair

    def updateFutureRounds(
        minSubmissions, maxSubmissions, restartDelay, timeout, oraclePayment
    ):
        return sp.variant(
            "updateFutureRounds",
            sp.record(
                minSubmissions=minSubmissions,
                maxSubmissions=maxSubmissions,
                restartDelay=restartDelay,
                timeout=timeout,
                oraclePayment=oraclePayment,
            ),
        )


MSAH = MSAggregatorHelper


class MSProxyHelper:
    def variant(content):
        return sp.variant.targetAdmin(content)

    def changeAggregator(aggregator):
        return sp.variant.changeAggregator(aggregator)

    def changeAdmin(admin):
        return sp.variant.changeAdmin(admin)

    def changeActive(active):
        return sp.variant.changeActive(active)


#########
# + Tests
#########
@sp.add_test()
def test():
    sc = sp.test_scenario("ChainlinkPriceFeed", [m, MSA.m2])
    sc.h1("ChainLink PriceFeed")

    FALSE_ADMIN_ADDRESS = sp.test_account("FALSE ADMIN").address

    sc.show(
        [
            ADMIN_ADDRESS,
            AGGREGATOR_ADDRESS,
            PROXY_ADDRESS,
            TOKEN_ADDRESS,
            ORACLE_1_ADDRESS,
            ORACLE_2_ADDRESS,
            ORACLE_3_ADDRESS,
            ORACLE_4_ADDRESS,
            ORACLE_5_ADDRESS,
            ORACLE_6_ADDRESS,
        ]
    )

    sc.h2("Link Token")
    linkToken = m.LinkToken(
        administrator=ADMIN_ADDRESS,
        metadata=sp.big_map(),
        ledger={ADMIN_ADDRESS: 50000000},
        token_metadata=FA2.make_metadata(
            name="wrapped LINK", decimals=18, symbol="wLINK"
        ),
    )
    sc += linkToken

    if sc.simulation_mode() is sp.SimulationMode.MOCKUP:
        sc.p("invalid b58 check in mockups")
        return

    sc.h2("Aggregator")
    restartDelay = sp.nat(2)
    now = sp.timestamp(500)
    oracles = {
        ORACLE_1_ADDRESS: sp.record(
            startingRound=0,
            endingRound=m.MAX_ROUND,
            lastStartedRound=0,
            withdrawable=0,
            adminAddress=ADMIN_ADDRESS,
        ),
        ORACLE_2_ADDRESS: sp.record(
            startingRound=0,
            endingRound=m.MAX_ROUND,
            lastStartedRound=0,
            withdrawable=0,
            adminAddress=ADMIN_ADDRESS,
        ),
        ORACLE_3_ADDRESS: sp.record(
            startingRound=0,
            endingRound=m.MAX_ROUND,
            lastStartedRound=0,
            withdrawable=0,
            adminAddress=ADMIN_ADDRESS,
        ),
        ORACLE_4_ADDRESS: sp.record(
            startingRound=0,
            endingRound=m.MAX_ROUND,
            lastStartedRound=0,
            withdrawable=0,
            adminAddress=ADMIN_ADDRESS,
        ),
    }
    aggregator = m.PriceAggregator(
        initialRoundDetails=sp.record(
            submissions={},
            minSubmissions=0,
            maxSubmissions=0,
            timeout=0,
            activeOracles=sp.set(),
        ),
        tokenAddress=linkToken.address,
        active=True,
        decimals=m.DECIMALS,
        admin=ADMIN_ADDRESS,
        oracles=oracles,
        timeout=m.TIMEOUT,
        oraclePayment=m.ORACLE_PAYMENT,
        minSubmissions=3,
        maxSubmissions=6,
        restartDelay=restartDelay,
        metadata=sp.big_map(),
    )
    sc += aggregator

    # Update aggregator available funds
    linkToken.transfer(
        [
            sp.record(
                from_=ADMIN_ADDRESS,
                txs=[
                    sp.record(
                        to_=aggregator.address,
                        amount=50000,
                        token_id=m.LINK_TOKEN_ID,
                    ),
                ],
            )
        ],
        _sender=ADMIN_ADDRESS,
    )
    aggregator.forceBalanceUpdate()
    sc.show(aggregator.data.recordedFunds)

    sc.h2("Proxy")
    latestRoundDataView = sp.contract(
        sp.address, AGGREGATOR_ADDRESS, entrypoint="latestRoundData"
    ).unwrap_some(error="Invalid Interface")
    proxy = m.Proxy(
        active=True,
        admin=ADMIN_ADDRESS,
        aggregator=sp.Some(sp.to_address(latestRoundDataView)),
    )
    sc += proxy

    sc.h2("Viewer")
    viewer = m.Viewer(ADMIN_ADDRESS, PROXY_ADDRESS)
    sc += viewer

    ###################################
    # A scenario with multiple rounds #
    ###################################

    # Round 1
    sc.h2("A complete round")
    roundId = 1
    price = 500
    sc.h3(f"Oracle 1 submits value in round {roundId}")
    now = now.add_minutes(1)
    aggregator.submit((roundId, price + 0), _sender=ORACLE_1_ADDRESS, _now=now)
    sc.h3(f"Oracle 2 submits value in round {roundId}")
    now = now.add_minutes(1)
    aggregator.submit((roundId, price + 5), _sender=ORACLE_2_ADDRESS, _now=now)
    sc.h3(f"Oracle 3 submits value in round {roundId}")
    now = now.add_minutes(1)
    aggregator.submit((roundId, price + 2), _sender=ORACLE_3_ADDRESS, _now=now)
    sc.h3(f"Quorum is reached in round {roundId}")
    # Verify answer value
    sc.verify(compute_latest_data(sc, aggregator).answer == price + 2)
    sc.verify(compute_latest_data(sc, aggregator).roundId == roundId)
    sc.verify(compute_latest_data(sc, aggregator).answeredInRound == roundId)
    sc.show(aggregator.data.rounds[aggregator.data.latestRoundId])
    sc.h3(f"Oracle 4 submits value in round {roundId}")
    now = now.add_minutes(1)
    aggregator.submit((roundId, price - 5), _sender=ORACLE_4_ADDRESS, _now=now)
    sc.h3(f"Answer is updated in round {roundId}")
    # Verify answer value
    sc.verify(compute_latest_data(sc, aggregator).answer == (price + price + 2) // 2)
    sc.verify(compute_latest_data(sc, aggregator).roundId == roundId)
    sc.verify(compute_latest_data(sc, aggregator).answeredInRound == roundId)
    sc.show(aggregator.data.rounds[aggregator.data.latestRoundId])
    sc.h3(f"Oracle 5 is not assigned")
    now = now.add_minutes(1)
    aggregator.submit((roundId, price - 5), _sender=ORACLE_5_ADDRESS, _valid=False)

    # Round 2
    sc.h2("A timed out round")
    roundId += 1
    price = 502
    sc.h3(f"Oracle 1 fails to start a new round {roundId}")
    now = now.add_minutes(1)
    aggregator.submit(
        (roundId, price + 0), _sender=ORACLE_1_ADDRESS, _now=now, _valid=False
    )
    sc.h3(f"Oracle 2 starts a new round {roundId + 1}")
    now = now.add_minutes(1)
    aggregator.submit((roundId, price + 1), _sender=ORACLE_2_ADDRESS, _now=now)

    # Round 3
    roundId += 1
    now = now.add_minutes(11)
    sc.h3(f"Round {roundId} timed out")
    sc.h2("A new round")
    sc.h3(f"Oracle 3 starts a new round in round {roundId}")
    aggregator.submit((roundId, price + 1), _sender=ORACLE_3_ADDRESS, _now=now)
    sc.h3(f"Oracle 1 fails to submit value in previous round {roundId - 1}, timed out")
    now = now.add_minutes(1)
    aggregator.submit((roundId - 1, price - 1), _sender=ORACLE_1_ADDRESS, _now=now)
    sc.h3(f"Quorum is reached in previous round {roundId - 1}")
    sc.verify(compute_latest_data(sc, aggregator).answer == price - 1)
    sc.verify(compute_latest_data(sc, aggregator).roundId == roundId - 2)
    sc.verify(compute_latest_data(sc, aggregator).answeredInRound == roundId - 2)

    sc.show(aggregator.data.rounds[aggregator.data.latestRoundId])
    sc.h3(f"Oracle 1 submits value in current round {roundId}")
    now = now.add_minutes(1)
    aggregator.submit((roundId, price + 2), _sender=ORACLE_1_ADDRESS, _now=now)
    sc.h3(f"Oracle 4 submits value in previous round {roundId - 1}")
    now = now.add_minutes(1)
    aggregator.submit((roundId, price + 3), _sender=ORACLE_4_ADDRESS, _now=now)
    sc.h3(f"Quorum was reached in round {roundId - 1}")
    sc.verify(compute_latest_data(sc, aggregator).answer == price + 2)
    sc.verify(compute_latest_data(sc, aggregator).roundId == roundId)
    sc.verify(compute_latest_data(sc, aggregator).answeredInRound == roundId)
    sc.show(aggregator.data.rounds[aggregator.data.latestRoundId])

    # Round 4
    sc.h2("A new round")
    roundId += 1
    price = 515
    sc.h3(f"Oracle 4 starts a new round {roundId}")
    now = now.add_minutes(1)
    aggregator.submit((roundId, price), _sender=ORACLE_4_ADDRESS, _now=now)
    sc.h3(f"Oracle 3 fails to start a new round because {roundId} isn't over")
    now = now.add_minutes(1)
    aggregator.submit(
        (roundId + 1, price), _sender=ORACLE_3_ADDRESS, _now=now, _valid=False
    )
    sc.h3(f"Oracle 1 submits value in current round {roundId}")
    now = now.add_minutes(1)
    aggregator.submit((roundId, price + 2), _sender=ORACLE_1_ADDRESS, _now=now)
    sc.show(aggregator.data.rounds[sp.as_nat(aggregator.data.latestRoundId - 1)])
    sc.h3(f"Oracle 2 submits value in previous round {roundId - 1}")
    now = now.add_minutes(1)
    aggregator.submit((roundId - 1, price - 10), _sender=ORACLE_2_ADDRESS, _now=now)
    sc.h3(f"Answer is updated in round {roundId - 1}")
    sc.verify(compute_latest_data(sc, aggregator).answer == 504)
    sc.verify(compute_latest_data(sc, aggregator).roundId == roundId - 1)
    sc.verify(compute_latest_data(sc, aggregator).answeredInRound == roundId)
    sc.show(aggregator.data.rounds[aggregator.data.latestRoundId])

    ##########
    # Withdraw oracle payment
    aggregator.withdrawPayment(
        oracleAddress=ORACLE_2_ADDRESS,
        recipientAddress=ORACLE_2_ADDRESS,
        amount=2,
        _sender=ADMIN_ADDRESS,
    )

    ##########
    # A viewer
    sc.h2("Viewer get latestRoundData")
    viewer.getLatestRoundData()

    #############################
    # Aggregator's administration

    sc.h2("Administration")
    sc.h3("False Admin tries to administrate")
    updateFutureRounds = MSAH.updateFutureRounds(
        restartDelay=2,
        minSubmissions=4,
        maxSubmissions=6,
        timeout=m.TIMEOUT,
        oraclePayment=m.ORACLE_PAYMENT,
    )
    aggregator.administrate(
        [updateFutureRounds], _sender=FALSE_ADMIN_ADDRESS, _valid=False
    )

    sc.h3("Admin sets Admin 2 as Admin")
    changeAdmin = MSAH.changeAdmin(FALSE_ADMIN_ADDRESS)
    aggregator.administrate([changeAdmin], _sender=ADMIN_ADDRESS)

    sc.h3("Admin 2 administrates futureRounds and removes Oracle2")
    updateFutureRounds = MSAH.updateFutureRounds(
        restartDelay=0,
        minSubmissions=2,
        maxSubmissions=4,
        timeout=m.TIMEOUT,
        oraclePayment=m.ORACLE_PAYMENT,
    )
    updateOracles = MSAH.changeOracles(removed=[ORACLE_2_ADDRESS])
    aggregator.administrate(
        [updateFutureRounds, updateOracles], _sender=FALSE_ADMIN_ADDRESS
    )

    ######################################
    # Administration via multisign admin #
    ######################################
    sc.h2("Multisign administration contract")
    now = now.add_minutes(1)
    multisignAdmin = MSA.m2.MultisignAdmin(
        quorum=1,
        timeout=5,
        addrVoterId=sp.big_map({ACCOUNT_1_ADDRESS: 0}),
        keyVoterId=sp.big_map({ACCOUNT_1_PUBLIC_KEY: 0}),
        voters={
            0: sp.record(
                addr=ACCOUNT_1_ADDRESS,
                publicKey=ACCOUNT_1_PUBLIC_KEY,
                lastProposalId=0,
            )
        },
        lastVoterId=0,
        metadata=sp.scenario_utils.metadata_of_url(
            "ipfs://QmWGLWx4pGZBrVF9Bz12pAT3A5Dunw3o9NMAKVvWK51Cfy"
        ),
    )
    sc += multisignAdmin

    sc.h2("Signers")
    sc.show([ACCOUNT_1_ADDRESS, ACCOUNT_2_ADDRESS])

    class signer1:
        address = ACCOUNT_1_ADDRESS

    class signer2:
        address = ACCOUNT_2_ADDRESS

    sc.h2("ACCOUNT_1 adds ACCOUNT_2, change quorum and set aggregator as target")
    changeVoters = MSA.SelfHelper.changeVoters(
        added=[(ACCOUNT_2_ADDRESS, ACCOUNT_2_PUBLIC_KEY)]
    )
    changeQuorum = MSA.SelfHelper.changeQuorum(2)
    targetAddress = sp.contract(
        sp.list[m.t_aggregatorAdminAction],
        aggregator.address,
        entrypoint="administrate",
    ).unwrap_some()
    changeTarget = MSA.SelfHelper.changeTarget(sp.to_address(targetAddress))
    multisignAdmin.newProposal(
        [changeVoters, changeQuorum, changeTarget],
        _sender=ACCOUNT_1_ADDRESS,
        _now=now,
    )

    sc.h2("Aggregator admin sets multisign as administrator")
    changeAdmin = MSAH.changeAdmin(multisignAdmin.address)
    aggregator.administrate([changeAdmin], _sender=FALSE_ADMIN_ADDRESS)

    sc.h2("Adding back Oracle2 via multisign")
    sc.h3("New Proposal by ACCOUNT_1")
    now = now.add_minutes(1)
    oracle2 = MSAH.oracle(ORACLE_2_ADDRESS, ADMIN_ADDRESS, roundId + 1)
    changeOracles = MSAH.changeOracles(added=[oracle2])
    multisignAdmin.newProposal(
        [MSAH.variant([changeOracles])], _sender=ACCOUNT_1_ADDRESS, _now=now
    )
    now = now.add_minutes(1)
    sc.h3("ACCOUNT_2 votes the proposal")
    sc.verify(~aggregator.data.oracles.contains(ORACLE_2_ADDRESS))
    multisignAdmin.vote(
        [MSA.vote(multisignAdmin, signer1, yay=True)], _sender=ACCOUNT_2_ADDRESS
    )
    sc.verify(aggregator.data.oracles.contains(ORACLE_2_ADDRESS))

    sc.h2("An administration proposal that fails on Aggregator")
    sc.h3("New Proposal by ACCOUNT_1")
    updateFutureRounds = MSAH.updateFutureRounds(10, 10, 10, 10, 10)
    multisignAdmin.newProposal(
        [MSAH.variant([updateFutureRounds])], _sender=ACCOUNT_1_ADDRESS, _now=now
    )
    now = now.add_minutes(1)
    sc.h3("ACCOUNT_2 votes the proposal")
    multisignAdmin.vote(
        [MSA.vote(multisignAdmin, signer1, yay=True)],
        _sender=ACCOUNT_2_ADDRESS,
        _valid=False,
    )
