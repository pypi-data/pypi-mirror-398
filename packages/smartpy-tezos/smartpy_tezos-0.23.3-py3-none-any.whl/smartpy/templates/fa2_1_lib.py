"""FA2.1 library - Work in progress...

Copyright (c) 2025 - present Trilitech Limited
Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

FA2.1 standard: https://gitlab.com/tezos/tzip/-/blob/master/proposals/tzip-26/tzip-26.md
Documentation: https://smartpy.tezos.com/manual/libraries/FA2-lib/overview.html
"""

import smartpy as sp
from smartpy.templates import fa2_types

t = fa2_types.t


@sp.module
def main():
    import t

    ##########
    # Events #
    ##########

    @sp.effects(with_operations=True)
    def transfer_event(e):
        sp.cast(e, t.transfer_event)
        sp.emit(sp.record(transfer_event=e), tag="transfer_event", with_type=True)

    @sp.effects(with_operations=True)
    def balance_update_event(e):
        sp.cast(e, t.balance_update_event)
        sp.emit(sp.record(balance_update_event=e), tag="balance_update", with_type=True)

    @sp.effects(with_operations=True)
    def allowance_update_event(e):
        sp.cast(e, t.allowance_update_event)
        sp.emit(
            sp.record(allowance_update_event=e), tag="allowance_update", with_type=True
        )

    @sp.effects(with_operations=True)
    def total_supply_update_event(e):
        sp.cast(e, t.total_supply_update_event)
        sp.emit(
            sp.record(total_supply_update=e), tag="total_supply_update", with_type=True
        )

    @sp.effects(with_operations=True)
    def operator_update_event(e):
        sp.cast(e, t.operator_update_event)
        sp.emit(sp.record(operator_update=e), tag="operator_update", with_type=True)

    @sp.effects(with_operations=True)
    def token_metadata_update_event(e):
        sp.cast(e, t.token_metadata_update_event)
        sp.emit(
            sp.record(token_metadata_update=e),
            tag="token_metadata_update",
            with_type=True,
        )

    ############
    # Policies #
    ############

    class NoTransfer(sp.Contract):
        """No transfer allowed."""

        def __init__(self):
            self.private.policy = sp.record(
                name="no-transfer",
                supports_transfer=False,
                supports_operator=False,
            )

        @sp.private()
        def check_operator_update_permissions_(self, operator_permission):
            sp.cast(operator_permission, t.operator_permission)
            raise "FA2_OPERATORS_UNSUPPORTED"
            return ()

        @sp.private()
        def check_spender_update_permissions_(self, spender_key):
            sp.cast(spender_key, t.spender_key)
            raise "FA2_OPERATORS_UNSUPPORTED"
            return ()

        @sp.private()
        def check_tx_transfer_permissions_(self, params):
            sp.cast(params, t.tx_transfer_request)
            raise "FA2_TX_DENIED"
            return ()

        @sp.private()
        def is_operator_(self, operator_permission):
            sp.cast(operator_permission, t.operator_permission)
            return False

    class OwnerTransfer(sp.Contract):
        """Only owner are allowed to transfer, no operators."""

        def __init__(self):
            self.private.policy = sp.record(
                name="owner-transfer",
                supports_transfer=True,
                supports_operator=False,
            )

        @sp.private()
        def check_operator_update_permissions_(self, operator_permission):
            sp.cast(operator_permission, t.operator_permission)
            raise "FA2_OPERATORS_UNSUPPORTED"
            return ()

        @sp.private()
        def check_spender_update_permissions_(self, spender_key):
            sp.cast(spender_key, t.spender_key)
            raise "FA2_OPERATORS_UNSUPPORTED"
            return ()

        @sp.private()
        def check_tx_transfer_permissions_(self, params):
            sp.cast(params, t.tx_transfer_request)
            assert sp.sender == params.from_, "FA2_NOT_OWNER"

        @sp.private()
        def is_operator_(self, operator_permission):
            sp.cast(operator_permission, t.operator_permission)
            return False

    class OwnerOrOperatorOrSpenderTransfer(sp.Contract):
        """Owner, operator or spender are allowed to transfer."""

        def __init__(self):
            self.private.policy = sp.record(
                name="owner-or-operator-transfer",
                supports_transfer=True,
                supports_operator=True,
            )
            self.data.operators = sp.cast(
                sp.big_map(), sp.big_map[t.operator_permission, sp.unit]
            )
            self.data.allowances = sp.cast(
                sp.big_map(),
                sp.big_map[t.spender_key, sp.nat],
            )

        @sp.private()
        def check_operator_update_permissions_(self, operator_permission):
            sp.cast(operator_permission, t.operator_permission)
            assert operator_permission.owner == sp.sender, "FA2_NOT_OWNER"

        @sp.private()
        def check_spender_update_permissions_(self, spender_key):
            sp.cast(spender_key, t.spender_key)
            assert spender_key.owner == sp.sender, "FA2_NOT_OWNER"

        @sp.private(with_storage="read-write")
        def check_tx_transfer_permissions_(self, param):
            sp.cast(param, t.tx_transfer_request)
            sp.cast(self.data.operators, sp.big_map[t.operator_permission, sp.unit])
            operator_permission = sp.record(
                owner=param.from_, operator=sp.sender, token_id=param.token_id
            )
            if param.from_ != sp.sender and not self.data.operators.contains(
                operator_permission
            ):
                allowance_key = sp.record(
                    owner=param.from_, spender=sp.sender, token_id=param.token_id
                )
                old_allowance = self.data.allowances.get(allowance_key, default=0)
                new_allowance = sp.as_nat(
                    old_allowance - param.amount,
                    error=("FA2_NOT_OPERATOR", "FA2.1_INSUFFICIENT_ALLOWANCE"),
                )
                self.data.allowances[allowance_key] = new_allowance

        @sp.private(with_storage="read-only")
        def is_operator_(self, operator_permission):
            sp.cast(self.data.operators, sp.big_map[t.operator_permission, sp.unit])
            return self.data.operators.contains(operator_permission)

    ##########
    # Common #
    ##########

    class CommonInterface(OwnerOrOperatorOrSpenderTransfer):
        def __init__(self):
            OwnerOrOperatorOrSpenderTransfer.__init__(self)
            self.data.token_metadata = sp.cast(sp.big_map(), t.token_metadata)
            self.data.metadata = sp.cast(sp.big_map(), t.metadata)
            self.data.next_token_id = 0

        @sp.private()
        def balance_(self, params):
            """Return the balance of an account.
            Must be redefined in child"""
            sp.cast(params, t.balance_params)
            raise "NotImplemented"
            return 0

        @sp.private()
        def is_defined_(self, token_id):
            """Return True if the token is defined, else otherwise.
            Must be redefined in child"""
            sp.cast(token_id, sp.nat)
            raise "NotImplemented"
            return False

        @sp.private(with_storage="read-write")
        def receive_tokens_(self, param):
            sp.cast(param, t.tx)
            raise "NotImplemented"
            return ()

        @sp.private(with_storage="read-write")
        def transfer_tx_(self, params):
            """Perform the transfer action.
            Must be redefined in child"""
            (receive_tokens, param) = params
            sp.cast(receive_tokens, t.receive_tokens_)
            sp.cast(param, t.transfer_tx_param)
            raise "NotImplemented"
            return ()

        @sp.private(with_storage="read-write")
        def export_ticket_(self, params):
            """Return a ticket that represents a token.
            Execute `check_tx_transfer_permissions_` on the request"""
            raise "NotImplemented"
            return sp.ticket((0, None), 1)

        @sp.private()
        def supply_(self, params):
            """Return the supply of a token.
            Must be redefined in child"""
            (is_defined, token_id) = params
            sp.cast(is_defined, t.is_defined_)
            sp.cast(token_id, sp.nat)
            raise "NotImplemented"
            return 0

        @sp.private()
        def emit_balance_delta(self, param):
            (balance, is_defined, updates) = param
            sp.cast(updates, t.balance_delta)
            raise "NotImplemented"
            return ()

    class Common(CommonInterface):
        """Common logic between Nft, Fungible and SingleAsset."""

        def __init__(self, metadata, sandbox):
            CommonInterface.__init__(self)
            self.data.metadata = sp.cast(metadata, t.metadata)
            self.data.sandbox = sp.cast(sandbox, sp.address)

        @sp.private(with_storage="read-only")
        def is_defined_(self, token_id):
            """Return True if the token is defined, else otherwise."""
            return self.data.token_metadata.contains(token_id)

        # Entrypoints

        @sp.entrypoint
        def update_operators(self, batch):
            """Accept a list of variants to add or remove operators.

            Operators can perform transfer on behalf of the owner without
            affecting the allowance.

            The person authorized to change the operator depends on the policy
            and is often restricted to the owner.

            Args:
                actions: List of operator update actions.
            Raises:
                `FA2_NOT_OWNER`
            Events: `"operator_update"`
            """
            sp.cast(batch, t.update_operators_param)
            if self.private.policy.supports_operator:
                operators_cache = {}
                for action in batch:
                    match action:
                        case add_operator(operator):
                            self.check_operator_update_permissions_(operator)
                            if not operators_cache.contains(operator):
                                operators_cache[operator] = (
                                    self.data.operators.contains(operator)
                                )
                            self.data.operators[operator] = ()
                        case remove_operator(operator):
                            self.check_operator_update_permissions_(operator)
                            if not operators_cache.contains(operator):
                                operators_cache[operator] = (
                                    self.data.operators.contains(operator)
                                )
                            del self.data.operators[operator]
                for operator in operators_cache.keys():
                    is_operator = self.data.operators.contains(operator)
                    if operators_cache[operator] != is_operator:
                        operator_update_event(
                            sp.record(
                                owner=operator.owner,
                                operator=operator.operator,
                                token_id=operator.token_id,
                                is_operator=is_operator,
                            )
                        )
            else:
                raise "FA2_OPERATORS_UNSUPPORTED"

        @sp.entrypoint
        def approve(self, batch):
            """Allow to increase or decrease the allowance set to `spender`
            regarding a token `owner` and a `token_id`.

            The `spender` can withdraw multiple times from the `owner`'s
            balance up to the set value.

            The person authorized to change the approval depends on the policy
            and is often restricted to the owner.

            Args:
                actions: List of approve update actions.
            Raises:
                `"FA2_NOT_OWNER"`
            Events: `"allowance_update"`
            """
            sp.cast(batch, t.approve_param)
            allowance_cache = {}
            for update in batch:
                allowance_key = sp.record(
                    owner=update.owner, spender=update.spender, token_id=update.token_id
                )
                self.check_spender_update_permissions_(allowance_key)
                old = self.data.allowances.get(allowance_key, default=0)
                if not allowance_cache.contains(allowance_key):
                    allowance_cache[allowance_key] = old
                match update.action:
                    case increase(amount):
                        if amount > 0:
                            self.data.allowances[allowance_key] = old + amount
                    case decrease(amount):
                        new_allowance = sp.as_nat(sp.max(old - amount, 0))
                        if new_allowance == 0:
                            del self.data.allowances[allowance_key]
                        else:
                            self.data.allowances[allowance_key] = new_allowance
            for allowance_key in allowance_cache.keys():
                old = allowance_cache[allowance_key]
                new = self.data.allowances.get(allowance_key, default=0)
                diff = new - old
                if diff != 0:
                    allowance_update_event(
                        sp.record(
                            owner=allowance_key.owner,
                            spender=allowance_key.spender,
                            token_id=allowance_key.token_id,
                            new_allowance=new,
                            diff=diff,
                        )
                    )

        @sp.entrypoint
        def balance_of(self, params):
            """Send the balance of multiple account / token pairs to a callback
            address.

            transfer 0 mutez to `callback` with corresponding response.

            `balance_` and `is_defined_` must be defined in the child class.

            Args:
                callback (contract): Where we callback the answer.
                requests: List of requested balances.
            Raises:
                `"FA2_TOKEN_UNDEFINED"`
            """
            sp.cast(params, t.balance_of_param)

            @sp.effects(with_storage="read-write")
            def f_process_request(param):
                (req, is_defined, balance) = param
                sp.cast(req, t.balance_of_request)
                return sp.cast(
                    sp.record(
                        request=req,
                        balance=balance((is_defined, req)),
                    ),
                    t.balance_of_response,
                )

            answers = [
                f_process_request((x, self.is_defined_, self.balance_))
                for x in params.requests
            ]
            sp.transfer(answers, sp.mutez(0), params.callback)

        @sp.entrypoint
        def transfer(self, batch):
            """Accept a list of transfer operations.

            Each transfer operation specifies a source: `from_` and a list
            of transactions. Each transaction specifies the destination: `to_`,
            the `token_id` and the `amount` to be transferred.

            `transfer_tx_` and `is_defined_` must be defined in the child class.

            Args:
                batch: List of transfer operations.
            Raises:
                `"FA2_TOKEN_UNDEFINED"`, `"FA2_NOT_OPERATOR"`,
                `"FA2.1_INSUFFICIENT_ALLOWANCE"`, `"FA2_INSUFFICIENT_BALANCE"`

            Events: `"transfer_event"`, `"balance_update"`, `"allowance_update"`
            """
            sp.cast(batch, t.transfer_param)
            if self.private.policy.supports_transfer:
                balances_delta = {}
                for transfer in batch:
                    for tx in transfer.txs:
                        # The ordering of assert is important:
                        # 1) token_undefined, 2) transfer permission 3) balance
                        assert self.is_defined_(tx.token_id), "FA2_TOKEN_UNDEFINED"
                        transfer_request = sp.record(
                            from_=transfer.from_, token_id=tx.token_id, amount=tx.amount
                        )
                        self.check_tx_transfer_permissions_(transfer_request)
                        if tx.amount > 0:
                            tx_params = sp.record(from_=transfer.from_, tx=tx)
                            self.transfer_tx_((self.receive_tokens_, tx_params))
                            ks = sp.record(owner=transfer.from_, token_id=tx.token_id)
                            kr = sp.record(owner=tx.to_, token_id=tx.token_id)
                            balances_delta[ks] = balances_delta.get(
                                ks, default=0
                            ) - sp.to_int(tx.amount)
                            balances_delta[kr] = sp.add(
                                balances_delta.get(kr, default=0), tx.amount
                            )
                        transfer_event(
                            sp.record(
                                from_=transfer.from_,
                                to_=tx.to_,
                                token_id=tx.token_id,
                                amount=tx.amount,
                            )
                        )
                self.emit_balance_delta(
                    (self.balance_, self.is_defined_, balances_delta)
                )
            else:
                raise "FA2_TX_DENIED"

        @sp.entrypoint
        def lambda_export(self, param):
            """Execute a lambda with a list of exported tickets representing tokens.

            Args:
                tickets_to_export (list): List of tickets to be exported.
                action (lambda): Lambda that takes a list of exported tickets and return a list of operations.
            Raises:
                `"FA2_TOKEN_UNDEFINED"`, `"FA2_NOT_OPERATOR"`,
                `"FA2.1_INSUFFICIENT_ALLOWANCE"`, `"FA2_INSUFFICIENT_BALANCE"`,
                `"FA2.1_SANDBOX_NOT_FOUND"`
            Events:
                `"allowance_update"`, `"balance_update"`
            """
            sp.cast(param, t.lambda_export_param)
            balances_delta = {}
            for t_arg in param.tickets_to_export:
                s = sp.record(owner=t_arg.from_, token_id=t_arg.token_id)
                balances_delta[s] = balances_delta.get(s, default=0) - sp.to_int(
                    t_arg.amount
                )
            # We loop again the tickets_to_export in order to create the
            # export list without duplicating tickets.
            export = [
                self.export_ticket_(
                    (self.is_defined_, (self.check_tx_transfer_permissions_, t_arg))
                )
                for t_arg in param.tickets_to_export
            ]
            sandbox = sp.contract(t.sandbox, self.data.sandbox).unwrap_some(
                error="FA2.1_INVALID_SANDBOX"  # The error should never be raised.
            )
            self.emit_balance_delta((self.balance_, self.is_defined_, balances_delta))
            # Transfer occurs after events emit.
            sp.transfer((export, param.action), sp.amount, sandbox)

        @sp.entrypoint
        def export_ticket(self, param):
            """Export a pair of `to` address and a list of tickets representing
            a token to a destination if provided or each ticket to the `to_` address.

            Args:
                destination (option of contract): Optional destination contract.
                txs: List of transactions with a `to_` address and `tickets_to_export` list of token to be exported.
            Raises:
                `"FA2_TOKEN_UNDEFINED"`, `"FA2_NOT_OPERATOR"`,
                `"FA2.1_INSUFFICIENT_ALLOWANCE"`, `"FA2_INSUFFICIENT_BALANCE"`,
                `"FA2.1_INVALID_DESTINATION"`
            Events:
                `"allowance_update"`, `"balance_update"`
            """
            sp.cast(param, t.export_ticket_param)
            balances_delta = {}
            transfer_operations = []
            match param.destination:
                case Some(contract):
                    for tx in param.txs:
                        for t_arg in tx.tickets_to_export:
                            s = sp.record(owner=t_arg.from_, token_id=t_arg.token_id)
                            balances_delta[s] = balances_delta.get(
                                s, default=0
                            ) - sp.to_int(t_arg.amount)
                    # We loop tickets_to_export a second time in order to create
                    # the export list without duplicating tickets.
                    export = [
                        (
                            tx.to_,
                            [
                                self.export_ticket_(
                                    (
                                        self.is_defined_,
                                        (
                                            self.check_tx_transfer_permissions_,
                                            t_arg,
                                        ),
                                    )
                                )
                                for t_arg in tx.tickets_to_export
                            ],
                        )
                        for tx in param.txs
                    ]
                    transfer_operations.push(
                        sp.transfer_operation(export, sp.tez(0), contract)
                    )
                case None:
                    for tx in param.txs:
                        contract = sp.contract(t.ticket, tx.to_).unwrap_some(
                            error="FA2.1_INVALID_DESTINATION"
                        )
                        for rq in tx.tickets_to_export:
                            t_arg = sp.record(
                                amount=rq.amount, from_=rq.from_, token_id=rq.token_id
                            )
                            ticket = self.export_ticket_(
                                (
                                    self.is_defined_,
                                    (self.check_tx_transfer_permissions_, t_arg),
                                )
                            )
                            s = sp.record(owner=rq.from_, token_id=rq.token_id)
                            balances_delta[s] = balances_delta.get(
                                s, default=0
                            ) - sp.to_int(rq.amount)
                            transfer_operations.push(
                                sp.transfer_operation(ticket, sp.tez(0), contract)
                            )
            self.emit_balance_delta((self.balance_, self.is_defined_, balances_delta))
            # Transfer operations are executed after the events.
            for operation in reversed(transfer_operations):
                sp.operations.push(operation)

        @sp.entrypoint
        def import_ticket(self, batch):
            """Import a pair of `to` address and a list of tickets representing
            a token.

            Args:
                destination (option of contract): Optional destination contract.
                txs: List of transactions with a `to_` address and `tickets_to_export` list of token to be exported.
            Raises:
                `"FA2.1_INVALID_TICKET"`, `"FA2_TOKEN_UNDEFINED"`
            Events:
                `"balance_update"`
            """
            sp.cast(batch, t.import_ticket_param)
            balances_delta = {}
            sp.cast(balances_delta, t.balance_delta)
            for el in batch:
                record(to_, tickets).match = el
                for ticket in tickets:
                    # Imported ticket is destroyed here.
                    # The standard allows it not to be destroyed under some circumstances.
                    (ticket_data, _) = sp.read_ticket(ticket)
                    # The standard allows to accept tickets from other contracts in some circumstances.
                    # We do not allow it here.
                    assert (
                        ticket_data.ticketer == sp.self_address
                    ), "FA2.1_INVALID_TICKET"
                    token_id = sp.fst(ticket_data.contents)
                    assert self.is_defined_(token_id), "FA2_TOKEN_UNDEFINED"
                    assert ticket_data.amount <= self.supply_(
                        (self.is_defined_, token_id)
                    ), (
                        "FA2.1_INVALID_TICKET",
                        "Ticket amount > supply.",
                    )
                    self.receive_tokens_(
                        sp.record(to_=to_, token_id=token_id, amount=ticket_data.amount)
                    )
                    r = sp.record(owner=to_, token_id=token_id)
                    balances_delta[r] = sp.add(
                        balances_delta.get(r, default=0), ticket_data.amount
                    )
            self.emit_balance_delta((self.balance_, self.is_defined_, balances_delta))

        # Onchain views

        @sp.onchain_view
        def get_balance(self, param: t.balance_of_request):
            """Return the balance of an address for the specified `token_id`."""
            return sp.record(balance=self.balance_((self.is_defined_, param)))

        @sp.onchain_view
        def get_total_supply(self, param):
            """Return the total number of tokens for the given `token_id` if known or
            fail if not."""
            return sp.record(total_supply=self.supply_((self.is_defined_, param)))

        @sp.onchain_view
        def is_operator(self, param):
            """Return whether `operator` is allowed to transfer `token_id` tokens
            owned by `owner`."""
            return sp.record(is_operator=self.data.operators.contains(param))

        @sp.onchain_view
        def get_allowance(self, param):
            """Returns the number of tokens `token_id` allowed by `owner` for `spender`."""
            return sp.record(allowance=self.data.allowances.get(param, default=0))

        @sp.onchain_view
        def get_token_metadata(self, param):
            """Returns the metadata associated to `token_id`."""
            return sp.record(
                token_info=self.data.token_metadata.get(
                    param.token_id,
                    default=sp.record(token_id=param.token_id, token_info={}),
                ).token_info
            )

        @sp.onchain_view
        def is_token(self, param):
            """Returns the metadata associated to `token_id`."""
            return sp.record(token_exist=self.is_defined_(param.token_id))

        # Offchain views

        @sp.offchain_view()
        def all_tokens(self):
            """Return the list of all the token IDs known to the contract."""
            return range(0, self.data.next_token_id)

        @sp.offchain_view()
        def is_operator(self, operator_permission):
            """Return whether `operator` is allowed to transfer `token_id` tokens
            owned by `owner`."""
            sp.cast(operator_permission, t.operator_permission)
            return self.is_operator_(operator_permission)

        @sp.offchain_view
        def get_balance(self, params):
            """Return the balance of an address for the specified `token_id`."""
            sp.cast(params, t.balance_of_request)
            return sp.record(balance=self.balance_((self.is_defined_, params)))

        @sp.offchain_view()
        def total_supply(self, params) -> sp.nat:
            """Return the total number of tokens for the given `token_id`."""
            supply = self.supply_((self.is_defined_, params.token_id))
            return supply

    ################
    # Base classes #
    ################

    class NftInterface(sp.Contract):
        def __init__(self):
            self.data.ledger = sp.cast(sp.big_map(), t.ledger_nft)
            self.private.ledger_type = "NFT"

    class Nft(NftInterface, Common):
        def __init__(self, metadata, ledger, token_metadata, sandbox):
            Common.__init__(self, metadata, sandbox)
            NftInterface.__init__(self)

            for token_info in token_metadata:
                self.data.token_metadata[self.data.next_token_id] = sp.record(
                    token_id=self.data.next_token_id, token_info=token_info
                )
                self.data.next_token_id += 1

            for token in ledger.items():
                assert self.data.token_metadata.contains(
                    token.key
                ), "The `ledger` parameter contains a key not contained in `token_metadata`."
                self.data.ledger[token.key] = token.value

        @sp.private(with_storage="read-only")
        def balance_(self, params):
            (is_defined, balance_params) = params
            assert is_defined(balance_params.token_id), "FA2_TOKEN_UNDEFINED"
            return (
                1
                if self.data.ledger.contains(balance_params.token_id)
                and self.data.ledger[balance_params.token_id] == balance_params.owner
                else 0
            )

        @sp.private(with_storage="read-write")
        def receive_tokens_(self, tx):
            sp.cast(tx, t.tx)
            # It's an NFT, we're never supposed to receive more than 1.
            assert tx.amount < 2
            # Don't do anything with amount being 0.
            if tx.amount > 0:
                self.data.ledger[tx.token_id] = tx.to_

        @sp.private(with_storage="read-write")
        def transfer_tx_(self, params):
            (receive_tokens, param) = params
            if param.tx.amount > 0:
                assert (
                    param.tx.amount == 1
                    and self.data.ledger[param.tx.token_id] == param.from_
                ), "FA2_INSUFFICIENT_BALANCE"
            receive_tokens(param.tx)

        @sp.private(with_storage="read-write")
        def export_ticket_(self, params):
            (is_defined, p2) = params
            (check_tx_transfer_permission, param) = p2
            assert is_defined(param.token_id), "FA2_TOKEN_UNDEFINED"
            check_tx_transfer_permission(param)
            # The standard allows to include an option of bytes along with the id.
            # Here we use None as there is no specific logic.
            content = (param.token_id, None)
            assert param.amount < 2, "FA2_INSUFFICIENT_BALANCE"
            assert (
                self.data.ledger.get(param.token_id, error="FA2_INSUFFICIENT_BALANCE")
                == param.from_
            ), "FA2_INSUFFICIENT_BALANCE"
            del self.data.ledger[param.token_id]
            # Tickets with an amount of 0 raises a runtime error.
            return sp.ticket(content, param.amount)

        @sp.private(with_storage="read-only")
        def supply_(self, params) -> sp.nat:
            (is_defined, token_id) = params
            assert is_defined(token_id), "FA2_TOKEN_UNDEFINED"
            return 1

        @sp.private(with_storage="read-write", with_operations=True)
        def emit_balance_delta(self, param):
            (balance, is_defined, updates) = param
            sp.cast(updates, t.balance_delta)
            for k in updates.keys():
                if updates[k] != 0:
                    balance_update_event(
                        sp.record(
                            owner=k.owner,
                            token_id=k.token_id,
                            new_balance=balance((is_defined, k)),
                            diff=updates[k],
                        )
                    )

    class FungibleInterface(sp.Contract):
        def __init__(self):
            self.private.ledger_type = "Fungible"
            self.data.ledger = sp.cast(sp.big_map(), t.ledger_fungible)
            self.data.supply = sp.cast(sp.big_map(), t.supply_fungible)

    class Fungible(FungibleInterface, Common):
        def __init__(self, metadata, ledger, token_metadata, sandbox):
            Common.__init__(self, metadata, sandbox)
            FungibleInterface.__init__(self)

            for token_info in token_metadata:
                token_id = self.data.next_token_id
                self.data.token_metadata[token_id] = sp.record(
                    token_id=token_id, token_info=token_info
                )
                self.data.supply[token_id] = 0
                self.data.next_token_id += 1

            for token in ledger.items():
                token_id = sp.snd(token.key)
                assert self.data.token_metadata.contains(
                    token_id
                ), "The `ledger` parameter contains a key not contained in `token_metadata`."
                self.data.supply[token_id] += token.value
                self.data.ledger[token.key] = token.value

        @sp.private(with_storage="read-only")
        def balance_(self, params):
            (is_defined, balance_params) = params
            assert is_defined(balance_params.token_id), "FA2_TOKEN_UNDEFINED"
            return self.data.ledger.get(
                (balance_params.owner, balance_params.token_id), default=0
            )

        @sp.private(with_storage="read-write")
        def receive_tokens_(self, tx):
            sp.cast(tx, t.tx)
            to_ = (tx.to_, tx.token_id)
            if tx.amount > 0:
                self.data.ledger[to_] = self.data.ledger.get(to_, default=0) + tx.amount

        @sp.private(with_storage="read-write")
        def transfer_tx_(self, params):
            (receive_tokens, param) = params
            # Makes the transfer
            from_ = (param.from_, param.tx.token_id)
            balance = self.data.ledger.get(from_, default=0) - param.tx.amount
            if balance == 0:
                del self.data.ledger[from_]
            else:
                self.data.ledger[from_] = sp.as_nat(
                    self.data.ledger.get(from_, default=0) - param.tx.amount,
                    error="FA2_INSUFFICIENT_BALANCE",
                )
            receive_tokens(param.tx)

        @sp.private(with_storage="read-write")
        def export_ticket_(self, params):
            (is_defined, p2) = params
            (check_tx_transfer_permission, param) = p2
            assert is_defined(param.token_id), "FA2_TOKEN_UNDEFINED"
            check_tx_transfer_permission(param)
            # The standard allows to include an option of bytes along with the id.
            # Here we use None as there is no specific logic.
            content = (param.token_id, None)
            from_ = (param.from_, param.token_id)
            self.data.ledger[from_] = sp.as_nat(
                self.data.ledger.get(from_, default=0) - param.amount,
                error="FA2_INSUFFICIENT_BALANCE",
            )
            # Tickets with an amount of 0 raises a runtime error.
            return sp.ticket(content, param.amount)

        @sp.private(with_storage="read-only")
        def supply_(self, params):
            (is_defined, token_id) = params
            assert is_defined(token_id), "FA2_TOKEN_UNDEFINED"
            return self.data.supply[token_id]

        @sp.private(with_storage="read-write", with_operations=True)
        def emit_balance_delta(self, param):
            (balance, is_defined, updates) = param
            sp.cast(updates, t.balance_delta)
            for k in updates.keys():
                if updates[k] != 0:
                    balance_update_event(
                        sp.record(
                            owner=k.owner,
                            token_id=k.token_id,
                            new_balance=balance((is_defined, k)),
                            diff=updates[k],
                        )
                    )

    class SingleAssetInterface(sp.Contract):
        def __init__(self):
            self.private.ledger_type = "SingleAsset"
            self.data.ledger = sp.cast(sp.big_map(), t.ledger_single_asset)
            self.data.supply = sp.cast(0, sp.nat)

    class SingleAsset(SingleAssetInterface, Common):
        def __init__(self, metadata, ledger, token_metadata, sandbox):
            Common.__init__(self, metadata, sandbox)
            SingleAssetInterface.__init__(self)

            self.data.token_metadata[0] = sp.record(
                token_id=0, token_info=token_metadata
            )
            for token in ledger.items():
                self.data.supply += token.value
                self.data.ledger[token.key] = token.value

        @sp.private(with_storage="read-only")
        def balance_(self, params):
            (is_defined, balance_params) = params
            assert is_defined(balance_params.token_id), "FA2_TOKEN_UNDEFINED"
            return self.data.ledger.get(balance_params.owner, default=0)

        @sp.private(with_storage="read-write")
        def receive_tokens_(self, tx):
            sp.cast(tx, t.tx)
            if tx.amount > 0:
                self.data.ledger[tx.to_] = (
                    self.data.ledger.get(tx.to_, default=0) + tx.amount
                )

        @sp.private(with_storage="read-write")
        def transfer_tx_(self, params):
            (receive_tokens, param) = params
            # Makes the transfer
            balance = self.data.ledger.get(param.from_, default=0) - param.tx.amount
            if balance == 0:
                del self.data.ledger[param.from_]
            else:
                self.data.ledger[param.from_] = sp.as_nat(
                    balance, error="FA2_INSUFFICIENT_BALANCE"
                )
            receive_tokens(param.tx)

        @sp.private(with_storage="read-write")
        def export_ticket_(self, params):
            (is_defined, p2) = params
            (check_tx_transfer_permission, param) = p2
            assert is_defined(param.token_id), "FA2_TOKEN_UNDEFINED"
            check_tx_transfer_permission(param)
            # The standard allows to include an option of bytes along with the id.
            # Here we use None as there is no specific logic.
            content = (param.token_id, None)
            from_ = param.from_
            self.data.ledger[from_] = sp.as_nat(
                self.data.ledger.get(from_, default=0) - param.amount,
                error="FA2_INSUFFICIENT_BALANCE",
            )
            # Tickets with an amount of 0 raises a runtime error.
            return sp.ticket(content, param.amount)

        @sp.private(with_storage="read-only")
        def supply_(self, params):
            (is_defined, token_id) = params
            assert is_defined(token_id), "FA2_TOKEN_UNDEFINED"
            return self.data.supply

        @sp.private(with_storage="read-write", with_operations=True)
        def emit_balance_delta(self, param):
            (balance, is_defined, updates) = param
            sp.cast(updates, t.balance_delta)
            for k in updates.keys():
                if updates[k] != 0:
                    balance_update_event(
                        sp.record(
                            owner=k.owner,
                            token_id=k.token_id,
                            new_balance=balance((is_defined, k)),
                            diff=updates[k],
                        )
                    )

    ##########
    # Mixins #
    ##########

    class AdminInterface(sp.Contract):
        def __init__(self):
            self.data.administrator = sp.address("")

        @sp.private()
        def is_administrator_(self):
            raise "NotImplemented"
            return False

    class Admin(sp.Contract):
        """(Mixin) Provide the basics for having an administrator in the contract.

        Adds an `administrator` attribute in the storage. Provides a
        `set_administrator` entrypoint.
        """

        def __init__(self, administrator):
            self.data.administrator = administrator

        @sp.private(with_storage="read-only")
        def is_administrator_(self):
            return sp.sender == self.data.administrator

        @sp.entrypoint
        def set_administrator(self, administrator):
            """(Admin only) Set the contract administrator."""
            assert self.is_administrator_(), "FA2_NOT_ADMIN"
            self.data.administrator = administrator

    class ChangeMetadata(AdminInterface):
        """(Mixin) Provide an entrypoint to change contract metadata.

        Requires the `Admin` mixin.
        """

        def __init__(self):
            AdminInterface.__init__(self)
            self.data.metadata = sp.cast(sp.big_map(), sp.big_map[sp.string, sp.bytes])

        @sp.entrypoint
        def set_metadata(self, metadata):
            """(Admin only) Set the contract metadata."""
            assert self.is_administrator_(), "FA2_NOT_ADMIN"
            self.data.metadata = metadata

    class WithdrawMutez(AdminInterface):
        """(Mixin) Provide an entrypoint to withdraw mutez that are in the
        contract's balance.

        Requires the `Admin` mixin.
        """

        def __init__(self):
            AdminInterface.__init__(self)

        @sp.entrypoint
        def withdraw_mutez(self, destination, amount):
            """(Admin only) Transfer `amount` mutez to `destination`."""
            assert self.is_administrator_(), "FA2_NOT_ADMIN"
            sp.send(destination, amount)

    class OffchainviewTokenMetadata(CommonInterface):
        """(Mixin) If present indexers use it to retrieve the token's metadata.

        Warning: If someone can change the contract's metadata they can change how
        indexers see every token metadata.
        """

        def __init__(self):
            CommonInterface.__init__(self)

        @sp.offchain_view()
        def token_metadata(self, token_id):
            """Returns the token-metadata URI for the given token."""
            assert self.data.token_metadata.contains(token_id), "FA2_TOKEN_UNDEFINED"
            return self.data.token_metadata[token_id]

    class OnchainviewBalanceOf(sp.Contract):
        """(Mixin) Non-standard onchain view equivalent to `balance_of`.

        Before onchain views were introduced in Michelson, the standard way
        of getting value from a contract was through a callback. Now that
        views are here we can create a view for the old style one.
        """

        @sp.private(with_storage="read-only")
        def balance_(self, params):
            raise "NotImplemented"
            return 0

        @sp.private(with_storage="read-only")
        def is_defined_(self, params):
            sp.cast(params, sp.nat)
            raise "NotImplemented"
            return False

        @sp.onchain_view()
        def get_balance_of(self, requests: sp.list[t.balance_of_request]):
            """Onchain view equivalent to the `balance_of` entrypoint."""
            # sp.cast(requests, sp.list[t.balance_of_request])

            @sp.effects(with_storage="read-only")
            def f_process_request_(param):
                (req, is_defined, balance) = param
                return sp.cast(
                    sp.record(
                        request=req,
                        balance=balance((is_defined, req)),
                    ),
                    t.balance_of_response,
                )

            return [
                f_process_request_((x, self.is_defined_, self.balance_))
                for x in requests
            ]

    class MintNft(AdminInterface, NftInterface, CommonInterface):
        """(Mixin) Non-standard `mint` entrypoint for FA2Nft with incrementing id.

        Requires the `Admin` mixin.
        """

        def __init__(self):
            CommonInterface.__init__(self)
            NftInterface.__init__(self)
            AdminInterface.__init__(self)

        @sp.entrypoint
        def mint(self, batch):
            """Admin can mint new or existing tokens."""
            sp.cast(
                batch,
                sp.list[
                    sp.record(
                        to_=sp.address,
                        metadata=sp.map[sp.string, sp.bytes],
                    ).layout(("to_", "metadata"))
                ],
            )
            assert self.is_administrator_(), "FA2_NOT_ADMIN"
            for action in batch:
                token_id = self.data.next_token_id
                self.data.token_metadata[token_id] = sp.record(
                    token_id=token_id, token_info=action.metadata
                )
                self.data.ledger[token_id] = action.to_
                self.data.next_token_id += 1
                total_supply_update_event(
                    sp.record(token_id=token_id, new_total_supply=1, diff=1)
                )
                balance_update_event(
                    sp.record(
                        owner=action.to_, token_id=token_id, diff=1, new_balance=1
                    )
                )
                token_metadata_update_event(
                    sp.record(token_id=token_id, new_metadata=sp.Some(action.metadata))
                )

    class MintFungible(AdminInterface, FungibleInterface, CommonInterface):
        """(Mixin) Non-standard `mint` entrypoint for FA2Fungible with incrementing
        id.

        Requires the `Admin` mixin.
        """

        def __init__(self):
            CommonInterface.__init__(self)
            FungibleInterface.__init__(self)
            AdminInterface.__init__(self)

        @sp.entrypoint
        def mint(self, batch):
            """Admin can mint tokens."""
            sp.cast(
                batch,
                sp.list[
                    sp.record(
                        to_=sp.address,
                        token=sp.variant(
                            new=sp.map[sp.string, sp.bytes], existing=sp.nat
                        ),
                        amount=sp.nat,
                    ).layout(("to_", ("token", "amount")))
                ],
            )
            assert self.is_administrator_(), "FA2_NOT_ADMIN"
            balances_delta = {}
            supply_delta = {}
            for action in batch:
                match action.token:
                    case new(metadata):
                        token_id = self.data.next_token_id
                        self.data.token_metadata[token_id] = sp.record(
                            token_id=token_id, token_info=metadata
                        )
                        self.data.supply[token_id] = action.amount
                        self.data.ledger[(action.to_, token_id)] = action.amount
                        self.data.next_token_id += 1
                        r = sp.record(owner=action.to_, token_id=token_id)
                        balances_delta[r] = sp.to_int(action.amount)
                        supply_delta[token_id] = sp.to_int(action.amount)
                        token_metadata_update_event(
                            sp.record(token_id=token_id, new_metadata=sp.Some(metadata))
                        )
                    case existing(token_id):
                        assert self.is_defined_(token_id), "FA2_TOKEN_UNDEFINED"
                        self.data.supply[token_id] += action.amount
                        from_ = (action.to_, token_id)
                        self.data.ledger[from_] = (
                            self.data.ledger.get(from_, default=0) + action.amount
                        )
                        r = sp.record(owner=action.to_, token_id=token_id)
                        balances_delta[r] = sp.add(
                            balances_delta.get(r, default=0), action.amount
                        )
                        supply_delta[token_id] = sp.add(
                            supply_delta.get(token_id, default=0), action.amount
                        )
            for token_id in supply_delta.keys():
                diff = supply_delta[token_id]
                if diff > 0:
                    total_supply_update_event(
                        sp.record(
                            token_id=token_id,
                            new_total_supply=self.data.supply[token_id],
                            diff=diff,
                        )
                    )
            self.emit_balance_delta((self.balance_, self.is_defined_, balances_delta))

    class MintSingleAsset(AdminInterface, SingleAssetInterface, CommonInterface):
        """(Mixin) Non-standard `mint` entrypoint for FA2SingleAsset.

        Requires the `Admin` mixin.
        """

        def __init__(self):
            CommonInterface.__init__(self)
            SingleAssetInterface.__init__(self)
            AdminInterface.__init__(self)

        @sp.entrypoint
        def mint(self, batch):
            """Admin can mint tokens."""
            sp.cast(
                batch,
                sp.list[
                    sp.record(to_=sp.address, amount=sp.nat).layout(("to_", "amount"))
                ],
            )
            assert self.is_administrator_(), "FA2_NOT_ADMIN"
            balances_delta = {}
            supply_delta = 0
            for action in batch:
                assert self.is_defined_(0), "FA2_TOKEN_UNDEFINED"
                self.data.supply += action.amount
                self.data.ledger[action.to_] = (
                    self.data.ledger.get(action.to_, default=0) + action.amount
                )
                r = sp.record(owner=action.to_, token_id=0)
                balances_delta[r] = sp.add(
                    balances_delta.get(r, default=0), action.amount
                )
                supply_delta += sp.to_int(action.amount)
            total_supply_update_event(
                sp.record(
                    token_id=0, new_total_supply=self.data.supply, diff=supply_delta
                )
            )
            self.emit_balance_delta((self.balance_, self.is_defined_, balances_delta))

    class BurnNft(AdminInterface, NftInterface, CommonInterface):
        """(Mixin) Non-standard `burn` entrypoint for FA2Nft that uses the transfer
        policy permission."""

        def __init__(self):
            CommonInterface.__init__(self)
            NftInterface.__init__(self)
            AdminInterface.__init__(self)

        @sp.entrypoint
        def burn(self, batch):
            """Users can burn tokens if they have the transfer policy permission.

            Burning an nft destroys its metadata.
            """
            sp.cast(
                batch,
                sp.list[
                    sp.record(
                        from_=sp.address,
                        token_id=sp.nat,
                        amount=sp.nat,
                    ).layout(("from_", ("token_id", "amount")))
                ],
            )
            assert self.private.policy.supports_transfer, "FA2_TX_DENIED"
            for action in batch:
                assert self.is_defined_(action.token_id), "FA2_TOKEN_UNDEFINED"
                self.check_tx_transfer_permissions_(
                    sp.record(
                        from_=action.from_,
                        token_id=action.token_id,
                        amount=action.amount,
                    )
                )
                if action.amount > 0:
                    assert (
                        (action.amount == 1)
                        and self.data.ledger.contains(action.token_id)
                        and (self.data.ledger[action.token_id] == action.from_)
                    ), "FA2_INSUFFICIENT_BALANCE"
                    # Burn the token
                    del self.data.ledger[action.token_id]
                    del self.data.token_metadata[action.token_id]
                    balance_update_event(
                        sp.record(
                            owner=action.from_,
                            token_id=action.token_id,
                            diff=-1,
                            new_balance=0,
                        )
                    )
                    total_supply_update_event(
                        sp.record(token_id=action.token_id, new_total_supply=0, diff=-1)
                    )
                    token_metadata_update_event(
                        sp.record(token_id=action.token_id, new_metadata=None)
                    )

    class BurnFungible(AdminInterface, FungibleInterface, CommonInterface):
        """(Mixin) Non-standard `burn` entrypoint for FA2Fungible that uses the
        transfer policy permission."""

        def __init__(self):
            CommonInterface.__init__(self)
            FungibleInterface.__init__(self)
            AdminInterface.__init__(self)

        @sp.entrypoint
        def burn(self, batch):
            """Users can burn tokens if they have the transfer policy
            permission."""
            sp.cast(
                batch,
                sp.list[
                    sp.record(
                        from_=sp.address,
                        token_id=sp.nat,
                        amount=sp.nat,
                    ).layout(("from_", ("token_id", "amount")))
                ],
            )
            assert self.private.policy.supports_transfer, "FA2_TX_DENIED"
            balances_delta = {}
            supply_cache = {}
            for action in batch:
                assert self.is_defined_(action.token_id), "FA2_TOKEN_UNDEFINED"
                self.check_tx_transfer_permissions_(
                    sp.record(
                        from_=action.from_,
                        token_id=action.token_id,
                        amount=action.amount,
                    )
                )
                if not supply_cache.contains(action.token_id):
                    supply_cache[action.token_id] = self.data.supply[action.token_id]
                from_ = (action.from_, action.token_id)
                # Burn the tokens
                new_balance = sp.as_nat(
                    self.data.ledger.get(from_, default=0) - action.amount,
                    error="FA2_INSUFFICIENT_BALANCE",
                )
                self.data.ledger[from_] = new_balance
                r = sp.record(owner=action.from_, token_id=action.token_id)
                balances_delta[r] = balances_delta.get(r, default=0) - sp.to_int(
                    action.amount
                )
                self.data.supply[action.token_id] = sp.as_nat(
                    self.data.supply.get(action.token_id, default=0) - action.amount,
                    error="FA2_INSUFFICIENT_BALANCE",
                )

            self.emit_balance_delta((self.balance_, self.is_defined_, balances_delta))
            for token_id in supply_cache.keys():
                old = supply_cache[token_id]
                new = self.data.supply[token_id]
                total_supply_update_event(
                    sp.record(token_id=token_id, new_total_supply=new, diff=new - old)
                )

    class BurnSingleAsset(AdminInterface, SingleAssetInterface, CommonInterface):
        """(Mixin) Non-standard `burn` entrypoint for FA2SingleAsset that uses the
        transfer policy permission."""

        def __init__(self):
            CommonInterface.__init__(self)
            SingleAssetInterface.__init__(self)
            AdminInterface.__init__(self)

        @sp.entrypoint
        def burn(self, batch):
            """Users can burn tokens if they have the transfer policy
            permission."""
            sp.cast(
                batch,
                sp.list[
                    sp.record(
                        from_=sp.address,
                        token_id=sp.nat,
                        amount=sp.nat,
                    ).layout(("from_", ("token_id", "amount")))
                ],
            )
            assert self.private.policy.supports_transfer, "FA2_TX_DENIED"
            balances_delta = {}
            old_supply = self.data.supply
            for action in batch:
                assert self.is_defined_(action.token_id), "FA2_TOKEN_UNDEFINED"
                self.check_tx_transfer_permissions_(
                    sp.record(
                        from_=action.from_,
                        token_id=action.token_id,
                        amount=action.amount,
                    )
                )
                # Burn the tokens
                new_balance = sp.as_nat(
                    self.data.ledger.get(action.from_, default=0) - action.amount,
                    error="FA2_INSUFFICIENT_BALANCE",
                )
                self.data.ledger[action.from_] = new_balance
                r = sp.record(owner=action.from_, token_id=action.token_id)
                balances_delta[r] = sp.add(
                    balances_delta.get(r, default=0), action.amount
                )
                self.data.supply = sp.as_nat(
                    self.data.supply - action.amount, error="FA2_INSUFFICIENT_SUPPLY"
                )

            self.emit_balance_delta((self.balance_, self.is_defined_, balances_delta))
            diff = self.data.supply - old_supply
            total_supply_update_event(
                sp.record(token_id=0, new_total_supply=self.data.supply, diff=diff)
            )


###########
# Helpers #
###########


@sp.module
def Helpers():
    import t

    class TestReceiverBalanceOf(sp.Contract):
        """Helper used to test the `balance_of` entrypoint.

        Don't use it on-chain as it can be gas locked.
        """

        def __init__(self):
            self.last_known_balances = sp.big_map()

        @sp.entrypoint
        def receive_balances(self, params):
            sp.cast(params, list[t.balance_of_response])
            for resp in params:
                owner = (resp.request.owner, resp.request.token_id)
                if self.data.last_known_balances.contains(sp.sender):
                    self.data.last_known_balances[sp.sender][owner] = resp.balance
                else:
                    self.data.last_known_balances[sp.sender] = {owner: resp.balance}


def make_metadata(symbol, name, decimals):
    """Helper function to build metadata JSON bytes values."""
    return sp.map(
        l={
            "decimals": sp.scenario_utils.bytes_of_string("%d" % decimals),
            "name": sp.scenario_utils.bytes_of_string(name),
            "symbol": sp.scenario_utils.bytes_of_string(symbol),
        }
    )
