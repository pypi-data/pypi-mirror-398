"""FA2 library testing module

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

Documentation: https://smartpy.tezos.com/manual/libraries/FA2-lib/overview.html
"""

from enum import Enum

import smartpy as sp


class Version(Enum):
    FA2 = 0
    FA2_1 = 1


admin = sp.test_account("Administrator")
admin2 = sp.test_account("Administrator2")
alice = sp.test_account("Alice")
bob = sp.test_account("Bob")
charlie = sp.test_account("Charlie")


def make_metadata(symbol, name, decimals):
    """Helper function to build metadata JSON bytes values."""
    return sp.map(
        l={
            "decimals": sp.scenario_utils.bytes_of_string("%d" % decimals),
            "name": sp.scenario_utils.bytes_of_string(name),
            "symbol": sp.scenario_utils.bytes_of_string(symbol),
        }
    )


tok0_md = make_metadata(name="Token Zero", decimals=1, symbol="Tok0")
tok1_md = make_metadata(name="Token One", decimals=1, symbol="Tok1")
tok2_md = make_metadata(name="Token Two", decimals=1, symbol="Tok2")

vector = lambda *arg: sp.scenario_utils.vector_raw(arg)


def ticket_data(ticketer, amount, contents):
    return sp.record(ticketer=ticketer, amount=amount, contents=contents)


@sp.module
def helpers():
    t_balance_of_response: type = sp.record(
        request=sp.record(owner=sp.address, token_id=sp.nat).layout(
            ("owner", "token_id")
        ),
        balance=sp.nat,
    ).layout(("request", "balance"))

    class TestReceiverBalanceOf(sp.Contract):
        """Helper used to test the `balance_of` entrypoint.

        Don't use it on-chain as it can be tricked.
        """

        def __init__(self):
            self.data.last_received_balances = []

        @sp.entrypoint
        def receive_balances(self, params):
            sp.cast(params, sp.list[t_balance_of_response])
            self.data.last_received_balances = params

    class Wallet(sp.Contract):
        @sp.entrypoint
        def default(self):
            pass


_helpers_fa2_1 = None


def get_helpers_fa2_1():
    # Get helpers for fa2_1 in a lazy way
    global _helpers_fa2_1
    if _helpers_fa2_1 is None:
        from smartpy.templates.fa2_lib_testing_fa2_1_helpers import (
            helpers_fa2_1 as helpers,
        )

        _helpers_fa2_1 = helpers

    return _helpers_fa2_1


################################################################################

# Standard features tests


def _get_balance(fa2, arg):
    return sp.View(fa2, "get_balance")(arg)


def _get_balance_fa2_1(fa2, arg):
    return _get_balance(fa2, arg).balance


def _get_balance_of(fa2, arg):
    return sp.View(fa2, "get_balance_of")(arg)


def _total_supply(fa2, arg):
    return sp.View(fa2, "total_supply")(arg)


def test_core_interfaces(
    class_, kwargs, ledger_type, test_name="", modules=None, version=Version.FA2
):
    """Test that each core interface has the right type and layout.

    Args:
        test_name (string): Name of the test
        fa2 (sp.Contract): The FA2 contract on which the tests occur.

    The contract must contains the tokens 0: tok0_md, 1: tok1_md, 2: tok2_md.

    For NFT contracts, `alice` must own the three tokens.

    For Fungible contracts, `alice` must own 42 of each token types.

    Tests:

    - Entrypoints: `balance_of`, `transfer`, `update_operators`
    - Storage: test of `token_metadata`
    """
    test_name = "test_core_interfaces_" + ledger_type + "_" + test_name
    modules = [] if modules is None else modules
    get_balance = _get_balance if version == Version.FA2 else _get_balance_fa2_1

    @sp.add_test()
    def test():
        sc = sp.test_scenario(test_name, modules)
        sc.add_module(helpers)
        if version == Version.FA2_1:
            sc.add_module(get_helpers_fa2_1())
        sc.h1(test_name)
        sc.p("A call to all the standard entrypoints and off-chain views.")

        sc.h2("Accounts")
        sc.show([admin, alice, bob])

        if version == Version.FA2_1:
            sc.h2("Sandbox")
            s = get_helpers_fa2_1().Sandbox()
            sc += s
            kwargs["sandbox"] = s.address

        sc.h2("FA2 contract")
        fa2 = class_(**kwargs)
        sc += fa2

        if sc.simulation_mode() is sp.SimulationMode.MOCKUP:
            sc.p("mockups - fix transfer based testing")
            return

        # Entrypoints

        sc.h2("Entrypoint: update_operators")
        fa2.update_operators(
            sp.set_type_expr(
                [
                    sp.variant(
                        "add_operator",
                        sp.record(
                            owner=alice.address, operator=alice.address, token_id=0
                        ),
                    )
                ],
                sp.list[
                    sp.variant(
                        add_operator=sp.record(
                            owner=sp.address, operator=sp.address, token_id=sp.nat
                        ).layout(("owner", ("operator", "token_id"))),
                        remove_operator=sp.record(
                            owner=sp.address, operator=sp.address, token_id=sp.nat
                        ).layout(("owner", ("operator", "token_id"))),
                    )
                ],
            ),
            _sender=alice,
        )

        sc.h2("Entrypoint: transfer")
        fa2.transfer(
            sp.set_type_expr(
                [
                    sp.record(
                        from_=alice.address,
                        txs=[sp.record(to_=alice.address, amount=1, token_id=0)],
                    )
                ],
                sp.list[
                    sp.record(
                        from_=sp.address,
                        txs=sp.list[
                            sp.record(
                                to_=sp.address, token_id=sp.nat, amount=sp.nat
                            ).layout(("to_", ("token_id", "amount")))
                        ],
                    ).layout(("from_", "txs"))
                ],
            ),
            _sender=alice,
        )

        sc.h2("Entrypoint: balance_of")
        sc.h3("Receiver contract")
        c2 = helpers.TestReceiverBalanceOf()
        sc += c2

        sc.h3("Call to balance_of")
        fa2.balance_of(
            sp.set_type_expr(
                sp.record(
                    callback=sp.contract(
                        sp.list[helpers.t_balance_of_response],
                        c2.address,
                        entrypoint="receive_balances",
                    ).unwrap_some(),
                    requests=[sp.record(owner=alice.address, token_id=0)],
                ),
                sp.record(
                    requests=sp.list[
                        sp.record(owner=sp.address, token_id=sp.nat).layout(
                            ("owner", "token_id")
                        )
                    ],
                    callback=sp.contract[
                        sp.list[
                            sp.record(
                                request=sp.record(
                                    owner=sp.address, token_id=sp.nat
                                ).layout(("owner", "token_id")),
                                balance=sp.nat,
                            ).layout(("request", "balance"))
                        ]
                    ],
                ).layout(("requests", "callback")),
            ),
            _sender=alice,
        )

        # Storage

        sc.h2("Storage: token_metadata")
        sc.verify_equal(
            fa2.data.token_metadata[0], sp.record(token_id=0, token_info=tok0_md)
        )


def test_transfer(
    class_, kwargs, ledger_type, test_name="", modules=None, version=Version.FA2
):
    """Test that transfer entrypoint works as expected.

    Do not test transfer permission policies.

    Args:
        test_name (string): Name of the test
        fa2 (sp.Contract): The FA2 contract on which the tests occur.

    SingleAsset contract: The contract must contains the token 0: tok0_md.
    Others: The contract must contains the tokens 0: tok0_md, 1: tok1_md, 2: tok2_md.

    NFT contract: `sp.test_account("Alice").address` must own all the tokens.
    Fungible contract: `sp.test_account("Alice").address` must own 42 of each token.

    Tests:
        - initial minting works as expected.
        - `get_balance` returns `balance = 0` for non owned tokens.
        - transfer of 0 tokens works when not owning tokens.
        - transfer of 0 doesn't change `ledger` storage.
        - transfer of 0 tokens works when owning tokens.
        - transfers with multiple operations and transactions works as expected.
        - fails with `FA2_INSUFFICIENT_BALANCE` when not enough balance.
        - transfer to self doesn't change anything.
        - transfer to self with more than balance gives `FA2_INSUFFICIENT_BALANCE`.
        - transfer to self of undefined token gives `FA2_TOKEN_UNDEFINED`.
        - transfer to someone else of undefined token gives `FA2_TOKEN_UNDEFINED`.
    """
    test_name = "test_transfer_" + ledger_type + "_" + test_name
    modules = [] if modules is None else modules
    get_balance = _get_balance if version == Version.FA2 else _get_balance_fa2_1

    @sp.add_test()
    def test():
        sc = sp.test_scenario(test_name, modules)
        # Origination is already tested in the `test_core_interfaces` function.
        if sc.simulation_mode() is sp.SimulationMode.MOCKUP:
            return
        if version == Version.FA2_1:
            sc.add_module(get_helpers_fa2_1())
        sc.h1(test_name)

        sc.h2("Accounts")
        sc.show([admin, alice, bob])

        if version == Version.FA2_1:
            sc.h2("Sandbox")
            s = get_helpers_fa2_1().Sandbox()
            sc += s
            kwargs["sandbox"] = s.address

        sc.h2("Contract")
        fa2 = class_(**kwargs)
        sc += fa2

        if ledger_type == "NFT":
            ICO = 1  # Initial coin offering.
            TX = 1  # How much we transfer at a time during the tests.
        else:
            ICO = 42  # Initial coin offering.
            TX = 12  # How much we transfer at a time during the tests.

        if sc.simulation_mode() is sp.SimulationMode.MOCKUP:
            sc.p("mockups - fix transfer based testing")
            return

        # Check that the contract storage is correctly initialized.
        sc.verify(get_balance(fa2, sp.record(owner=alice.address, token_id=0)) == ICO)
        if not ledger_type == "SingleAsset":
            sc.verify(
                get_balance(fa2, sp.record(owner=alice.address, token_id=1)) == ICO
            )
            sc.verify(
                get_balance(fa2, sp.record(owner=alice.address, token_id=2)) == ICO
            )

        # Check that the balance is interpreted as zero when the owner doesn't hold any.
        # TZIP-12: If the token owner does not hold any tokens of type token_id,
        #          the owner's balance is interpreted as zero.
        sc.verify(get_balance(fa2, sp.record(owner=bob.address, token_id=0)) == 0)

        sc.h2("Zero amount transfer")
        sc.p("TZIP-12: Transfers of zero amount MUST be treated as normal transfers.")

        # Check that someone with 0 token can transfer 0 token.
        fa2.transfer(
            [
                sp.record(
                    from_=bob.address,
                    txs=[sp.record(to_=alice.address, amount=0, token_id=0)],
                ),
            ],
            _sender=bob,
        )

        # Check that the contract storage is unchanged.
        sc.verify(get_balance(fa2, sp.record(owner=alice.address, token_id=0)) == ICO)
        sc.verify(get_balance(fa2, sp.record(owner=bob.address, token_id=0)) == 0)

        # Check that someone with some tokens can transfer 0 token.
        fa2.transfer(
            [
                sp.record(
                    from_=alice.address,
                    txs=[sp.record(to_=bob.address, amount=0, token_id=0)],
                ),
            ],
            _sender=alice,
        )

        # Check that the contract storage is unchanged.
        sc.verify(get_balance(fa2, sp.record(owner=alice.address, token_id=0)) == ICO)
        sc.verify(get_balance(fa2, sp.record(owner=bob.address, token_id=0)) == 0)

        sc.h2("Transfers Alice -> Bob")
        sc.p(
            """TZIP-12: Each transfer in the batch MUST decrement token balance
                of the source (from_) address by the amount of the transfer and
                increment token balance of the destination (to_) address by the
                amount of the transfer."""
        )

        # Perform a complex transfer with 2 operations, one of which contains 2 transactions.
        if ledger_type == "SingleAsset":
            fa2.transfer(
                [
                    sp.record(
                        from_=alice.address,
                        txs=[
                            sp.record(to_=bob.address, amount=TX // 3, token_id=0),
                            sp.record(to_=bob.address, amount=TX // 3, token_id=0),
                        ],
                    ),
                    sp.record(
                        from_=alice.address,
                        txs=[sp.record(to_=bob.address, amount=TX // 3, token_id=0)],
                    ),
                ],
                _sender=alice,
            )
        else:
            fa2.transfer(
                [
                    sp.record(
                        from_=alice.address,
                        txs=[
                            sp.record(to_=bob.address, amount=TX, token_id=0),
                            sp.record(to_=bob.address, amount=TX, token_id=1),
                        ],
                    ),
                    sp.record(
                        from_=alice.address,
                        txs=[sp.record(to_=bob.address, amount=TX, token_id=2)],
                    ),
                ],
                _sender=alice,
            )

        # Check that the contract storage is correctly updated.
        sc.verify(
            get_balance(fa2, sp.record(owner=alice.address, token_id=0)) == ICO - TX
        )
        sc.verify(get_balance(fa2, sp.record(owner=bob.address, token_id=0)) == TX)

        if not ledger_type == "SingleAsset":
            sc.verify(
                get_balance(fa2, sp.record(owner=alice.address, token_id=1)) == ICO - TX
            )
            sc.verify(get_balance(fa2, sp.record(owner=bob.address, token_id=1)) == TX)

        # Check without using get_balance because the ledger interface
        # differs between NFT and fungible.
        if ledger_type == "NFT":
            sc.verify(fa2.data.ledger[0] == bob.address)
        else:
            if ledger_type == "Fungible":
                sc.verify(fa2.data.ledger[(alice.address, 0)] == ICO - TX)
                sc.verify(fa2.data.ledger[(bob.address, 0)] == TX)
            else:
                sc.verify(fa2.data.ledger[alice.address] == ICO - TX)
                sc.verify(fa2.data.ledger[bob.address] == TX)

        # Error tests

        # test of FA2_INSUFFICIENT_BALANCE.
        sc.h2("Insufficient balance")
        sc.p(
            """TIP-12: If the transfer amount exceeds current token balance of
                the source address, the whole transfer operation MUST fail with
                the error mnemonic "FA2_INSUFFICIENT_BALANCE"."""
        )

        # Compute bob_balance to transfer 1 more token.
        bob_balance = sc.compute(
            get_balance(fa2, sp.record(owner=bob.address, token_id=0))
        )

        # Test that a complex transfer with only one insufficient
        # balance fails.
        fa2.transfer(
            [
                sp.record(
                    from_=bob.address,
                    txs=[
                        sp.record(
                            to_=alice.address, amount=bob_balance + 1, token_id=0
                        ),
                        sp.record(to_=alice.address, amount=0, token_id=0),
                    ],
                ),
                sp.record(
                    from_=bob.address,
                    txs=[sp.record(to_=alice.address, amount=0, token_id=0)],
                ),
            ],
            _sender=bob,
            _valid=False,
            _exception="FA2_INSUFFICIENT_BALANCE",
        )

        sc.h2("Same address transfer")
        sc.p(
            """TZIP-12: Transfers with the same address (from_ equals to_) MUST
                be treated as normal transfers."""
        )

        # Test that someone can transfer all his balance to itself
        # without problem.
        fa2.transfer(
            [
                sp.record(
                    from_=bob.address,
                    txs=[sp.record(to_=bob.address, amount=bob_balance, token_id=0)],
                ),
            ],
            _sender=bob,
        )

        # Check that the contract storage is unchanged.
        sc.verify(
            get_balance(fa2, sp.record(owner=alice.address, token_id=0)) == ICO - TX
        )
        sc.verify(get_balance(fa2, sp.record(owner=bob.address, token_id=0)) == TX)
        if not ledger_type == "SingleAsset":
            sc.verify(
                get_balance(fa2, sp.record(owner=alice.address, token_id=1)) == ICO - TX
            )
            sc.verify(get_balance(fa2, sp.record(owner=bob.address, token_id=1)) == TX)

        # Test that someone cannot transfer more tokens than he holds
        # even to himself.
        fa2.transfer(
            [
                sp.record(
                    from_=bob.address,
                    txs=[
                        sp.record(to_=bob.address, amount=bob_balance + 1, token_id=0)
                    ],
                ),
            ],
            _sender=bob,
            _valid=False,
            _exception="FA2_INSUFFICIENT_BALANCE",
        )

        # test of FA2_TOKEN_UNDEFINED.
        sc.h2("Not defined token")
        sc.p(
            """TZIP-12: If one of the specified token_ids is not defined within
                the FA2 contract, the entrypoint MUST fail with the error
                mnemonic "FA2_TOKEN_UNDEFINED"."""
        )

        # A transfer of 0 tokens to self gives FA2_TOKEN_UNDEFINED if
        # not defined.
        fa2.transfer(
            [
                sp.record(
                    from_=bob.address,
                    txs=[sp.record(to_=bob.address, amount=0, token_id=4)],
                ),
            ],
            _sender=bob,
            _valid=False,
            _exception="FA2_TOKEN_UNDEFINED",
        )

        # A transfer of 1 token to someone else gives
        # FA2_TOKEN_UNDEFINED if not defined.
        fa2.transfer(
            [
                sp.record(
                    from_=alice.address,
                    txs=[sp.record(to_=bob.address, amount=1, token_id=4)],
                ),
            ],
            _sender=bob,
            _valid=False,
            _exception="FA2_TOKEN_UNDEFINED",
        )


def test_balance_of(
    class_, kwargs, ledger_type, test_name="", modules=None, version=Version.FA2
):
    """Test that balance_of entrypoint works as expected.

    Args:
        test_name (string): Name of the test
        fa2 (sp.Contract): The FA2 contract on which the tests occur.

    SingleAsset contract: The contract must contains the token 0: tok0_md.
    Others: The contract must contains the tokens 0: tok0_md, 1: tok1_md, 2: tok2_md.

    NFT contract: `sp.test_account("Alice").address` must own all the tokens.
    Fungible contract: `sp.test_account("Alice").address` must own 42 of each token.

    Tests:

    - `balance_of` calls back with valid results.
    - `balance_of` fails with `FA2_TOKEN_UNDEFINED` when token is undefined.
    """
    test_name = "test_balance_of_" + ledger_type + "_" + test_name
    modules = [] if modules is None else modules
    get_balance = _get_balance if version == Version.FA2 else _get_balance_fa2_1

    @sp.add_test()
    def test():
        sc = sp.test_scenario(test_name, modules)
        # Origination is already tested in the `test_core_interfaces` function.
        if sc.simulation_mode() is sp.SimulationMode.MOCKUP:
            return
        sc.add_module(helpers)
        if version == Version.FA2_1:
            sc.add_module(get_helpers_fa2_1())
        sc.h1(test_name)

        sc.h2("Accounts")
        sc.show([admin, alice, bob])

        if version == Version.FA2_1:
            sc.h2("Sandbox")
            s = get_helpers_fa2_1().Sandbox()
            sc += s
            kwargs["sandbox"] = s.address

        # We initialize the contract with an initial mint.
        sc.h2("Contract")
        fa2 = class_(**kwargs)
        sc += fa2

        sc.h3("Receiver contract")
        c2 = helpers.TestReceiverBalanceOf()
        sc += c2

        if sc.simulation_mode() is sp.SimulationMode.MOCKUP:
            sc.p("mockups - fix transfer based testing")
            return

        ICO = 1 if ledger_type == "NFT" else 42  # Initial coin offering.
        last_token_id = 0 if ledger_type == "SingleAsset" else 2

        requests = [
            sp.record(owner=alice.address, token_id=0),
            sp.record(owner=alice.address, token_id=0),
            sp.record(owner=bob.address, token_id=0),
            sp.record(owner=alice.address, token_id=last_token_id),
        ]
        expected = [
            sp.record(balance=ICO, request=sp.record(owner=alice.address, token_id=0)),
            sp.record(balance=ICO, request=sp.record(owner=alice.address, token_id=0)),
            sp.record(balance=0, request=sp.record(owner=bob.address, token_id=0)),
            sp.record(
                balance=ICO,
                request=sp.record(owner=alice.address, token_id=last_token_id),
            ),
        ]

        # Call to balance_of.
        fa2.balance_of(
            callback=sp.contract(
                sp.list[helpers.t_balance_of_response],
                c2.address,
                entrypoint="receive_balances",
            ).unwrap_some(),
            requests=requests,
            _sender=alice,
        )

        # Check that balance_of returns the correct balances.
        # This test non-deduplication, non-reordering, on multiple tokens.
        sc.verify_equal(c2.data.last_received_balances, expected)

        # Expected errors
        sc.h2("FA2_TOKEN_UNDEFINED error")
        fa2.balance_of(
            callback=sp.contract(
                sp.list[helpers.t_balance_of_response],
                c2.address,
                entrypoint="receive_balances",
            ).unwrap_some(),
            requests=[
                sp.record(owner=alice.address, token_id=0),
                sp.record(owner=alice.address, token_id=5),
            ],
            _sender=alice,
            _valid=False,
            _exception="FA2_TOKEN_UNDEFINED",
        )


def test_no_transfer(
    class_, kwargs, ledger_type, test_name="", modules=None, version=Version.FA2
):
    """Test that the `no-transfer` policy works as expected.

    Args:
        test_name (string): Name of the test
        fa2 (sp.Contract): The FA2 contract on which the tests occur.

    The contract must contains the tokens 0: tok0_md, 1: tok1_md, 2: tok2_md.

    For NFT contracts, `alice` must own the three tokens.

    For Fungible contracts, `alice` must own 42 of each token types.

    Tests:

    - transfer fails with FA2_TX_DENIED.
    - transfer fails with FA2_TX_DENIED even for admin.
    - update_operators fails with FA2_OPERATORS_UNSUPPORTED.
    """
    test_name = "test_no-transfer_" + ledger_type + "_" + test_name
    modules = [] if modules is None else modules
    get_balance = _get_balance if version == Version.FA2 else _get_balance_fa2_1

    @sp.add_test()
    def test():
        sc = sp.test_scenario(test_name, modules)
        sc.h1(test_name)

        sc.h2("Accounts")
        sc.show([admin, alice, bob])

        if version == Version.FA2_1:
            sc.add_module(get_helpers_fa2_1())
            sc.h2("Sandbox")
            s = get_helpers_fa2_1().Sandbox()
            sc += s
            kwargs["sandbox"] = s.address

        sc.h2("FA2 with NoTransfer policy")
        sc.p("No transfer are allowed.")
        fa2 = class_(**kwargs)
        sc += fa2

        # Transfer fails as expected.
        sc.h2("Alice cannot transfer: FA2_TX_DENIED")
        fa2.transfer(
            [
                sp.record(
                    from_=alice.address,
                    txs=[sp.record(to_=bob.address, amount=1, token_id=0)],
                )
            ],
            _sender=alice,
            _valid=False,
            _exception="FA2_TX_DENIED",
        )

        # Even Admin cannot transfer.
        sc.h2("Admin cannot transfer alice's token: FA2_TX_DENIED")
        fa2.transfer(
            [
                sp.record(
                    from_=alice.address,
                    txs=[sp.record(to_=alice.address, amount=1, token_id=0)],
                )
            ],
            _sender=admin,
            _valid=False,
            _exception="FA2_TX_DENIED",
        )

        # update_operators is unsupported.
        sc.h2("Alice cannot add operator: FA2_OPERATORS_UNSUPPORTED")
        fa2.update_operators(
            [
                sp.variant(
                    "add_operator",
                    sp.record(owner=alice.address, operator=bob.address, token_id=0),
                )
            ],
            _sender=alice,
            _valid=False,
            _exception="FA2_OPERATORS_UNSUPPORTED",
        )


def test_owner_transfer(
    class_, kwargs, ledger_type, test_name="", modules=None, version=Version.FA2
):
    """Test that the `owner-transfer` policy works as expected.

    Args:
        test_name (string): Name of the test
        fa2 (sp.Contract): the FA2 contract on which the tests occur.

    The contract must contains the tokens 0: tok0_md, 1: tok1_md, 2: tok2_md.

    For NFT contracts, `alice` must own the three tokens.

    For Fungible contracts, `alice` must own 42 of each token types.

    Tests:

    - owner can transfer.
    - transfer fails with FA2_NOT_OWNER for non owner, even admin.
    - update_operators fails with FA2_OPERATORS_UNSUPPORTED.
    """
    test_name = "test_owner-transfer_" + ledger_type + "_" + test_name
    modules = [] if modules is None else modules
    get_balance = _get_balance if version == Version.FA2 else _get_balance_fa2_1

    @sp.add_test()
    def test():
        sc = sp.test_scenario(test_name, modules)
        sc.h1(test_name)

        sc.h2("Accounts")
        sc.show([admin, alice, bob])

        if version == Version.FA2_1:
            sc.add_module(get_helpers_fa2_1())
            sc.h2("Sandbox")
            s = get_helpers_fa2_1().Sandbox()
            sc += s
            kwargs["sandbox"] = s.address

        sc.h2("FA2 with OwnerTransfer policy")
        sc.p("Only owner can transfer, no operator allowed.")
        fa2 = class_(**kwargs)
        sc += fa2

        # The owner can transfer its tokens.
        sc.h2("Alice can transfer")
        fa2.transfer(
            [
                sp.record(
                    from_=alice.address,
                    txs=[sp.record(to_=alice.address, amount=1, token_id=0)],
                )
            ],
            _sender=alice,
        )

        # Admin cannot transfer someone else tokens.
        sc.h2("Admin cannot transfer alice's token: FA2_NOT_OWNER")
        fa2.transfer(
            [
                sp.record(
                    from_=alice.address,
                    txs=[sp.record(to_=alice.address, amount=1, token_id=0)],
                )
            ],
            _sender=admin,
            _valid=False,
            _exception="FA2_NOT_OWNER",
        )

        # Someone cannot transfer someone else tokens.
        sc.h2("Admin cannot transfer alice's token: FA2_NOT_OWNER")
        fa2.transfer(
            [
                sp.record(
                    from_=alice.address,
                    txs=[sp.record(to_=alice.address, amount=1, token_id=0)],
                )
            ],
            _sender=bob,
            _valid=False,
            _exception="FA2_NOT_OWNER",
        )

        # Someone cannot add operator.
        sc.h2("Alice cannot add operator: FA2_OPERATORS_UNSUPPORTED")
        fa2.update_operators(
            [
                sp.variant(
                    "add_operator",
                    sp.record(owner=alice.address, operator=bob.address, token_id=0),
                )
            ],
            _sender=alice,
            _valid=False,
            _exception="FA2_OPERATORS_UNSUPPORTED",
        )


def test_owner_or_operator_transfer(
    class_, kwargs, ledger_type, test_name="", modules=None, version=Version.FA2
):
    """Test that the `owner-or-operator-transfer` policy works as expected.

    Args:
        test_name (string): Name of the test
        fa2 (sp.Contract): The FA2 contract on which the tests occur.

    SingleAsset contract: The contract must contains the token 0: tok0_md.
    Others: The contract must contains the tokens 0: tok0_md, 1: tok1_md, 2: tok2_md.

    NFT contract: `sp.test_account("Alice").address` must own all the tokens.
    Fungible contract: `sp.test_account("Alice").address` must own 42 of each token.

    Tests:

    - owner can transfer.
    - transfer fails with FA2_NOT_OPERATOR or FA2.1_INSUFFICIENT_ALLOWANCE for non operator, even admin.
    - update_operators fails with FA2_OPERATORS_UNSUPPORTED.
    - owner can add operator.
    - operator can transfer.
    - operator cannot transfer for non allowed `token_id`.
    - owner can remove operator and add operator in a batch.
    - removed operator cannot transfer anymore.
    - operator added in a batch can transfer.
    - add then remove the same operator doesn't change the storage.
    - remove then add the same operator does change the storage.
    """
    test_name = "test_owner-or-operator-transfer_" + ledger_type + "_" + test_name
    modules = [] if modules is None else modules
    get_balance = _get_balance if version == Version.FA2 else _get_balance_fa2_1

    @sp.add_test()
    def test():
        operator_bob = sp.record(owner=alice.address, operator=bob.address, token_id=0)
        operator_charlie = sp.record(
            owner=alice.address, operator=charlie.address, token_id=0
        )

        sc = sp.test_scenario(test_name, modules)
        if version == Version.FA2_1:
            sc.add_module(get_helpers_fa2_1())
        sc.h1(test_name)

        sc.h2("Accounts")
        sc.show([admin, alice, bob])

        if version == Version.FA2_1:
            sc.h2("Sandbox")
            s = get_helpers_fa2_1().Sandbox()
            sc += s
            kwargs["sandbox"] = s.address

        sc.h2("FA2 with OwnerOrOperatorTransfer policy")
        sc.p("Owner or operators can transfer.")
        fa2 = class_(**kwargs)
        sc += fa2

        if sc.simulation_mode() is sp.SimulationMode.MOCKUP:
            sc.p("mockups - fix transfer based testing")
            return

        # Owner can transfer his tokens.
        sc.h2("Alice can transfer")
        fa2.transfer(
            [
                sp.record(
                    from_=alice.address,
                    txs=[sp.record(to_=alice.address, amount=1, token_id=0)],
                )
            ],
            _sender=alice,
        )

        # Admin cannot transfer others tokens.
        sc.h2("Admin cannot transfer alice's token: FA2_NOT_OPERATOR")
        exception = (
            ("FA2_NOT_OPERATOR", "FA2.1_INSUFFICIENT_ALLOWANCE")
            if version == Version.FA2_1
            else "FA2_NOT_OPERATOR"
        )
        fa2.transfer(
            [
                sp.record(
                    from_=alice.address,
                    txs=[sp.record(to_=alice.address, amount=1, token_id=0)],
                )
            ],
            _sender=admin,
            _valid=False,
            _exception=exception,
        )

        # Update operator works.
        sc.h2("Alice adds Bob as operator")
        fa2.update_operators([sp.variant.add_operator(operator_bob)], _sender=alice)

        # The contract is updated as expected.
        sc.verify(fa2.data.operators.contains(operator_bob))

        # Operator can transfer allowed tokens on behalf of owner.
        sc.h2("Bob can transfer Alice's token id 0")
        fa2.transfer(
            [
                sp.record(
                    from_=alice.address,
                    txs=[sp.record(to_=alice.address, amount=1, token_id=0)],
                )
            ],
            _sender=bob,
        )

        if not ledger_type == "SingleAsset":
            # Operator cannot transfer not allowed tokens on behalf of owner.
            sc.h2("Bob cannot transfer Alice's token id 1")
            fa2.transfer(
                [
                    sp.record(
                        from_=alice.address,
                        txs=[sp.record(to_=alice.address, amount=1, token_id=1)],
                    )
                ],
                _sender=bob,
                _valid=False,
                _exception=exception,
            )

        # Batch of update_operators actions.
        sc.h2("Alice can remove Bob as operator and add Charlie")
        fa2.update_operators(
            [
                sp.variant.remove_operator(operator_bob),
                sp.variant.add_operator(operator_charlie),
            ],
            _sender=alice,
        )

        # The contract is updated as expected.
        sc.verify(~fa2.data.operators.contains(operator_bob))
        sc.verify(fa2.data.operators.contains(operator_charlie))

        # A removed operator lose its rights.
        sc.h2("Bob cannot transfer Alice's token 0 anymore")
        fa2.transfer(
            [
                sp.record(
                    from_=alice.address,
                    txs=[sp.record(to_=alice.address, amount=1, token_id=0)],
                )
            ],
            _sender=bob,
            _valid=False,
            _exception=exception,
        )

        # The new added operator can now do the transfer.
        sc.h2("Charlie can transfer Alice's token")
        fa2.transfer(
            [
                sp.record(
                    from_=alice.address,
                    txs=[sp.record(to_=charlie.address, amount=1, token_id=0)],
                )
            ],
            _sender=charlie,
        )

        # The contract is updated as expected.
        sc.verify(get_balance(fa2, sp.record(owner=charlie.address, token_id=0)) == 1)

        # Remove after a Add does nothing.
        sc.h2("Add then Remove in the same batch is transparent")
        sc.p(
            """TZIP-12: If two different commands in the list add and remove an
                operator for the same token owner and token ID, the last command
                in the list MUST take effect."""
        )
        fa2.update_operators(
            [
                sp.variant.add_operator(operator_bob),
                sp.variant.remove_operator(operator_bob),
            ],
            _sender=alice,
        )
        sc.verify(~fa2.data.operators.contains(operator_bob))

        # Add after remove works
        sc.h2("Remove then Add do add the operator")
        fa2.update_operators(
            [
                sp.variant.remove_operator(operator_bob),
                sp.variant.add_operator(operator_bob),
            ],
            _sender=alice,
        )
        sc.verify(fa2.data.operators.contains(operator_bob))


################################################################################

# FA2.1 tests


class Fa2_1:
    def test_approve(
        class_, kwargs, ledger_type, version: Version, test_name="", modules=None
    ):
        """Test that the approve entrypoint works as expected.

        Tests:

        - allowance batch including increase and decrease works as expected.
        - allowance decreased below zero is zeroed.
        """
        if version != Version.FA2_1:
            raise AttributeError("test_approve only works for FA2.1")
        test_name = "test_approve_" + ledger_type + "_" + test_name
        modules = [] if modules is None else modules

        @sp.add_test()
        def test():
            sc = sp.test_scenario(test_name, modules)
            # Origination is already tested in the `test_core_interfaces` function.
            if sc.simulation_mode() is sp.SimulationMode.MOCKUP:
                return
            sc.add_module(get_helpers_fa2_1())
            sc.h1(test_name)

            sc.h2("Accounts")
            sc.show([admin, alice, bob])

            sc.h2("Sandbox")
            s = get_helpers_fa2_1().Sandbox()
            sc += s
            kwargs["sandbox"] = s.address

            sc.h2("FA2 contract")
            fa2 = class_(**kwargs)
            sc += fa2

            if sc.simulation_mode() is sp.SimulationMode.MOCKUP:
                sc.p("mockups - fix transfer based testing")
                return

            allowance_bob = sp.record(
                owner=alice.address, spender=bob.address, token_id=0
            )
            allowance_charlie = sp.record(
                owner=alice.address, spender=charlie.address, token_id=0
            )

            sc.h2("Allowance batch works as expected")
            fa2.approve(
                [
                    sp.record(
                        owner=alice.address,
                        spender=bob.address,
                        token_id=0,
                        action=sp.variant.increase(43),
                    ),
                    sp.record(
                        owner=alice.address,
                        spender=bob.address,
                        token_id=0,
                        action=sp.variant.decrease(1),
                    ),
                    sp.record(
                        owner=alice.address,
                        spender=charlie.address,
                        token_id=0,
                        action=sp.variant.increase(1),
                    ),
                    sp.record(
                        owner=alice.address,
                        spender=charlie.address,
                        token_id=0,
                        action=sp.variant.decrease(1),
                    ),
                ],
                _sender=alice,
            )
            sc.verify(fa2.data.allowances[allowance_bob] == 42)
            sc.verify(~fa2.data.allowances.contains(allowance_charlie))
            fa2.approve(
                [
                    sp.record(
                        owner=alice.address,
                        spender=bob.address,
                        token_id=0,
                        action=sp.variant.decrease(24),
                    ),
                ],
                _sender=alice,
            )
            sc.verify(fa2.data.allowances[allowance_bob] == 18)

            sc.h2("Allowance decreased below zero is zeroed")
            fa2.approve(
                [
                    sp.record(
                        owner=alice.address,
                        spender=bob.address,
                        token_id=0,
                        action=sp.variant.decrease(1337),
                    ),
                ],
                _sender=alice,
            )
            sc.verify(~fa2.data.allowances.contains(allowance_bob))

    def test_approve_only_owner(
        class_, kwargs, ledger_type, version: Version, test_name="", modules=None
    ):
        """Test the allowance policy which restrict allowance action to the owner.

        Tests:

        - non owner cannot set allowance
        - owner can set allowance
        """
        if version != Version.FA2_1:
            raise AttributeError("test_approve_only_owner only works for FA2.1")
        test_name = "test_approve_only_owner" + ledger_type + "_" + test_name
        modules = [] if modules is None else modules

        @sp.add_test()
        def test():
            sc = sp.test_scenario(test_name, modules)
            sc.add_module(get_helpers_fa2_1())
            sc.h1(test_name)

            sc.h2("Accounts")
            sc.show([admin, alice, bob])

            sc.h2("Sandbox")
            s = get_helpers_fa2_1().Sandbox()
            sc += s
            kwargs["sandbox"] = s.address

            sc.h2("FA2 contract")
            fa2 = class_(**kwargs)
            sc += fa2

            if sc.simulation_mode() is sp.SimulationMode.MOCKUP:
                sc.p("mockups - fix transfer based testing")
                return

            sc.h2("Owner can set owner")
            fa2.approve(
                [
                    sp.record(
                        owner=alice.address,
                        spender=bob.address,
                        token_id=0,
                        action=sp.variant.increase(1),
                    ),
                ],
                _sender=bob,
                _valid=False,
                _exception="FA2_NOT_OWNER",
            )

            sc.h2("Non owner cannot set owner")
            fa2.approve(
                [
                    sp.record(
                        owner=alice.address,
                        spender=bob.address,
                        token_id=0,
                        action=sp.variant.increase(1),
                    ),
                ],
                _sender=alice,
            )

    def test_transfer_allowance(
        class_, kwargs, ledger_type, version: Version, test_name="", modules=None
    ):
        """Test that the transfer entrypoint works with the allowance system as expected.

        Tests:
        - non set allowance allows transfer of zero.
        - transfer fails with `("FA2_NOT_OPERATOR", "FA2.1_INSUFFICIENT_ALLOWANCE")` when allowance is insufficient.
        - transfer by non operators decreases allowance.
        - transfer by owner doesn't require allowance.
        - transfer by operators doesn't decrease allowance.
        """
        if version != Version.FA2_1:
            raise AttributeError("test_transfer_allowance only works for FA2.1")
        test_name = "test_transfer_allowance" + ledger_type + "_" + test_name
        modules = [] if modules is None else modules

        @sp.add_test()
        def test():
            sc = sp.test_scenario(test_name, modules)
            # Origination is already tested in the `test_core_interfaces` function.
            if sc.simulation_mode() is sp.SimulationMode.MOCKUP:
                return
            sc.add_module(get_helpers_fa2_1())
            sc.h1(test_name)

            sc.h2("Accounts")
            sc.show([admin, alice, bob])

            sc.h2("Sandbox")
            s = get_helpers_fa2_1().Sandbox()
            sc += s
            kwargs["sandbox"] = s.address

            sc.h2("FA2 contract")
            fa2 = class_(**kwargs)
            sc += fa2

            if sc.simulation_mode() is sp.SimulationMode.MOCKUP:
                sc.p("mockups - fix transfer based testing")
                return

            allowance_bob = sp.record(
                owner=alice.address, spender=bob.address, token_id=0
            )
            operator_bob = sp.record(
                owner=alice.address, operator=bob.address, token_id=0
            )

            # Non set allowance allows transfer of zero
            fa2.transfer(
                [
                    sp.record(
                        from_=alice.address,
                        txs=[
                            sp.record(to_=bob.address, amount=0, token_id=0),
                        ],
                    )
                ],
                _sender=bob,
            )

            amount = 1 if ledger_type == "NFT" else 10

            # transfer fails with FA2.1_INSUFFICIENT_ALLOWANCE when allowance is insufficient.

            fa2.transfer(
                [
                    sp.record(
                        from_=alice.address,
                        txs=[
                            sp.record(to_=bob.address, amount=amount, token_id=0),
                        ],
                    )
                ],
                _sender=bob,
                _valid=False,
                _exception=("FA2_NOT_OPERATOR", "FA2.1_INSUFFICIENT_ALLOWANCE"),
            )

            # transfer by non operators decreases allowance.

            fa2.approve(
                [
                    sp.record(
                        owner=alice.address,
                        spender=bob.address,
                        token_id=0,
                        action=sp.variant.increase(42),
                    ),
                ],
                _sender=alice,
            )
            sc.verify(fa2.data.allowances[allowance_bob] == 42)

            fa2.transfer(
                [
                    sp.record(
                        from_=alice.address,
                        txs=[
                            sp.record(to_=bob.address, amount=amount, token_id=0),
                        ],
                    )
                ],
                _sender=bob,
            )
            sc.verify(fa2.data.allowances[allowance_bob] == 42 - amount)

            # transfer by owner doesn't require allowance.
            fa2.transfer(
                [
                    sp.record(
                        from_=bob.address,
                        txs=[
                            sp.record(to_=alice.address, amount=amount, token_id=0),
                        ],
                    )
                ],
                _sender=bob,
            )

            # transfer by operators doesn't decrease allowance.

            fa2.update_operators([sp.variant.add_operator(operator_bob)], _sender=alice)
            fa2.transfer(
                [
                    sp.record(
                        from_=alice.address,
                        txs=[
                            sp.record(to_=bob.address, amount=amount, token_id=0),
                        ],
                    )
                ],
                _sender=bob,
            )
            sc.verify(fa2.data.allowances[allowance_bob] == 42 - amount)

    def test_export_ticket(
        class_, kwargs, ledger_type, version: Version, test_name="", modules=None
    ):
        """Test that the export_ticket entrypoint works as expected.

        Tests:

        - export of undefined token
        - export with insufficient balance
        - export with a destination
        - export without a destination and invalid `tx.to_`
        - export without a destination
        - balance is decreased for sender and not increased for receiver
        """
        if version != Version.FA2_1:
            raise AttributeError("test_export_ticket only works for FA2.1")
        test_name = "test_export_ticket_" + ledger_type + "_" + test_name
        get_balance = _get_balance_fa2_1
        modules = [] if modules is None else modules

        @sp.add_test()
        def test():
            sc = sp.test_scenario(test_name, modules)
            # Origination is already tested in the `test_core_interfaces` function.
            if sc.simulation_mode() is sp.SimulationMode.MOCKUP:
                return
            sc.add_module(get_helpers_fa2_1())
            sc.h1(test_name)

            sc.h2("Accounts")
            sc.show([admin, alice, bob])

            sc.h2("Sandbox")
            s = get_helpers_fa2_1().Sandbox()
            sc += s
            kwargs["sandbox"] = s.address

            sc.h2("FA2 contract")
            fa2 = class_(**kwargs)
            sc += fa2

            if sc.simulation_mode() is sp.SimulationMode.MOCKUP:
                sc.p("mockups - TODO Ticket in unauthorized position (type error)")
                return

            sc.h2("Ticket receiver contracts")
            receiver_1 = get_helpers_fa2_1().Receiver()
            sc += receiver_1
            receiver_2 = get_helpers_fa2_1().Receiver()
            sc += receiver_2

            # Export with a destination
            sc.h2("Destination receiver helper contract")
            destination_receiver = get_helpers_fa2_1().DestinationReceiver()
            sc += destination_receiver

            destination = sp.contract(
                sp.list[sp.pair[sp.address, sp.list[get_helpers_fa2_1().t_ticket]]],
                destination_receiver.address,
            )
            sc.h2("Undefined token")
            fa2.export_ticket(
                destination=destination,
                txs=[
                    sp.record(
                        to_=receiver_1.address,
                        tickets_to_export=[
                            sp.record(from_=alice.address, amount=1, token_id=4)
                        ],
                    ),
                ],
                _sender=alice,
                _valid=False,
                _exception="FA2_TOKEN_UNDEFINED",
            )

            sc.h2("Export with insufficient balance")
            alice_balance = get_balance(fa2, sp.record(owner=alice.address, token_id=0))
            sc.verify(alice_balance > 0)
            fa2.export_ticket(
                destination=destination,
                txs=[
                    sp.record(
                        to_=receiver_1.address,
                        tickets_to_export=[
                            sp.record(
                                from_=alice.address,
                                amount=alice_balance + 1,
                                token_id=0,
                            )
                        ],
                    ),
                ],
                _sender=alice,
                _valid=False,
                _exception="FA2_INSUFFICIENT_BALANCE",
            )

            sc.h2("Export ticket with a destination")
            if ledger_type == "SingleAsset":
                fa2.export_ticket(
                    destination=destination,
                    txs=[
                        sp.record(
                            to_=receiver_1.address,
                            tickets_to_export=[
                                sp.record(from_=alice.address, amount=1, token_id=0),
                                sp.record(from_=alice.address, amount=20, token_id=0),
                            ],
                        ),
                        sp.record(
                            to_=receiver_2.address,
                            tickets_to_export=[
                                sp.record(from_=alice.address, amount=1, token_id=0)
                            ],
                        ),
                        sp.record(
                            to_=receiver_1.address,
                            tickets_to_export=[
                                sp.record(from_=alice.address, amount=1, token_id=0)
                            ],
                        ),
                    ],
                    _sender=alice,
                )
                destination_receiver.check(
                    vector(
                        (
                            receiver_1.address,
                            vector(
                                ticket_data(fa2.address, 1, (0, None)),
                                ticket_data(fa2.address, 20, (0, None)),
                            ),
                        ),
                        (
                            receiver_2.address,
                            vector(ticket_data(fa2.address, 1, (0, None))),
                        ),
                        (
                            receiver_1.address,
                            vector(ticket_data(fa2.address, 1, (0, None))),
                        ),
                    )
                )
                # Sender balance is decreased
                sc.verify(
                    get_balance(fa2, sp.record(owner=alice.address, token_id=0))
                    == 42 - 23
                )
                # Receiver balance is not increased
                sc.verify(
                    get_balance(fa2, sp.record(owner=receiver_1.address, token_id=0))
                    == 0
                )
                sc.verify(
                    get_balance(fa2, sp.record(owner=receiver_2.address, token_id=0))
                    == 0
                )
                # # Total supply doesn't change
                sc.verify(_total_supply(fa2, sp.record(token_id=0)) == 42)
            elif ledger_type == "NFT":
                fa2.export_ticket(
                    destination=destination,
                    txs=[
                        sp.record(
                            to_=receiver_1.address,
                            tickets_to_export=[
                                sp.record(from_=alice.address, amount=1, token_id=0),
                                sp.record(from_=alice.address, amount=1, token_id=1),
                            ],
                        ),
                        sp.record(
                            to_=receiver_2.address,
                            tickets_to_export=[
                                sp.record(from_=alice.address, amount=1, token_id=2),
                            ],
                        ),
                    ],
                    _sender=alice,
                )
                destination_receiver.check(
                    vector(
                        (
                            receiver_1.address,
                            vector(
                                ticket_data(fa2.address, 1, (0, None)),
                                ticket_data(fa2.address, 1, (1, None)),
                            ),
                        ),
                        (
                            receiver_2.address,
                            vector(ticket_data(fa2.address, 1, (2, None))),
                        ),
                    )
                )
                # Sender balance is decreased
                sc.verify(
                    get_balance(fa2, sp.record(owner=alice.address, token_id=0)) == 0
                )
                sc.verify(
                    get_balance(fa2, sp.record(owner=alice.address, token_id=1)) == 0
                )
                sc.verify(
                    get_balance(fa2, sp.record(owner=alice.address, token_id=2)) == 0
                )
                # Receiver balance is not increased
                sc.verify(
                    get_balance(fa2, sp.record(owner=receiver_1.address, token_id=0))
                    == 0
                )
                sc.verify(
                    get_balance(fa2, sp.record(owner=receiver_1.address, token_id=1))
                    == 0
                )
                sc.verify(
                    get_balance(fa2, sp.record(owner=receiver_2.address, token_id=2))
                    == 0
                )
                # Total supply doesn't change
                sc.verify(_total_supply(fa2, sp.record(token_id=0)) == 1)
                sc.verify(_total_supply(fa2, sp.record(token_id=1)) == 1)
                sc.verify(_total_supply(fa2, sp.record(token_id=2)) == 1)
            else:
                fa2.export_ticket(
                    destination=sp.contract(
                        sp.list[
                            sp.pair[sp.address, sp.list[get_helpers_fa2_1().t_ticket]]
                        ],
                        destination_receiver.address,
                    ),
                    txs=[
                        sp.record(
                            to_=receiver_1.address,
                            tickets_to_export=[
                                sp.record(from_=alice.address, amount=1, token_id=0),
                                sp.record(from_=alice.address, amount=20, token_id=0),
                                sp.record(from_=alice.address, amount=1, token_id=1),
                            ],
                        ),
                        sp.record(
                            to_=receiver_2.address,
                            tickets_to_export=[
                                sp.record(from_=alice.address, amount=1, token_id=0)
                            ],
                        ),
                        sp.record(
                            to_=receiver_1.address,
                            tickets_to_export=[
                                sp.record(from_=alice.address, amount=1, token_id=0)
                            ],
                        ),
                    ],
                    _sender=alice,
                )
                destination_receiver.check(
                    vector(
                        (
                            receiver_1.address,
                            vector(
                                ticket_data(fa2.address, 1, (0, None)),
                                ticket_data(fa2.address, 20, (0, None)),
                                ticket_data(fa2.address, 1, (1, None)),
                            ),
                        ),
                        (
                            receiver_2.address,
                            vector(ticket_data(fa2.address, 1, (0, None))),
                        ),
                        (
                            receiver_1.address,
                            vector(ticket_data(fa2.address, 1, (0, None))),
                        ),
                    )
                )
                # Sender balance is decreased
                sc.verify(
                    get_balance(fa2, sp.record(owner=alice.address, token_id=0))
                    == 42 - 23
                )
                sc.verify(
                    get_balance(fa2, sp.record(owner=alice.address, token_id=1))
                    == 42 - 1
                )
                # Receiver balance is not increased
                sc.verify(
                    get_balance(fa2, sp.record(owner=receiver_1.address, token_id=0))
                    == 0
                )
                sc.verify(
                    get_balance(fa2, sp.record(owner=receiver_1.address, token_id=1))
                    == 0
                )
                sc.verify(
                    get_balance(fa2, sp.record(owner=receiver_2.address, token_id=0))
                    == 0
                )
                # Total supply doesn't change
                sc.verify(_total_supply(fa2, sp.record(token_id=0)) == 42)

            # Export with an invalid `tx.to_`
            sc.h2("Export ticket with an invalid `tx.to_`")
            fa2.export_ticket(
                destination=None,
                txs=[
                    sp.record(
                        to_=fa2.address,
                        tickets_to_export=[
                            sp.record(from_=alice.address, amount=0, token_id=0),
                        ],
                    ),
                ],
                _sender=alice,
                _valid=False,
                _exception="FA2.1_INVALID_DESTINATION",
            )

            # Export without a destination
            sc.h2("Export ticket without a destination")
            if ledger_type == "SingleAsset":
                fa2.export_ticket(
                    destination=None,
                    txs=[
                        sp.record(
                            to_=receiver_1.address,
                            tickets_to_export=[
                                sp.record(from_=alice.address, amount=1, token_id=0),
                                sp.record(from_=alice.address, amount=10, token_id=0),
                            ],
                        ),
                        sp.record(
                            to_=receiver_2.address,
                            tickets_to_export=[
                                sp.record(from_=alice.address, amount=1, token_id=0)
                            ],
                        ),
                        sp.record(
                            to_=receiver_1.address,
                            tickets_to_export=[
                                sp.record(from_=alice.address, amount=1, token_id=0)
                            ],
                        ),
                    ],
                    _sender=alice,
                )
                receiver_1.check(
                    vector(
                        ticket_data(fa2.address, 1, (0, None)),
                        ticket_data(fa2.address, 10, (0, None)),
                        ticket_data(fa2.address, 1, (0, None)),
                    )
                )
                sc.verify(receiver_1.data.id == 3)
                receiver_2.check(vector(ticket_data(fa2.address, 1, (0, None))))
                sc.verify(receiver_2.data.id == 1)
            elif ledger_type == "NFT":
                fa2.export_ticket(
                    destination=None,
                    txs=[
                        sp.record(to_=receiver_1.address, amount=1, token_id=0),
                        sp.record(to_=receiver_2.address, amount=1, token_id=1),
                        sp.record(to_=receiver_1.address, amount=1, token_id=2),
                    ],
                )
                receiver_1.check(
                    vector(
                        ticket_data(fa2.address, 1, (0, None)),
                        ticket_data(fa2.address, 1, (2, None)),
                    )
                )
                sc.verify(receiver_1.data.id == 2)
                receiver_2.check(vector(ticket_data(fa2.address, 1, (1, None))))
                sc.verify(receiver_2.data.id == 1)
            else:
                fa2.export_ticket(
                    destination=None,
                    txs=[
                        sp.record(
                            to_=receiver_1.address,
                            tickets_to_export=[
                                sp.record(from_=alice.address, amount=1, token_id=0),
                                sp.record(from_=alice.address, amount=10, token_id=0),
                                sp.record(from_=alice.address, amount=1, token_id=1),
                            ],
                        ),
                        sp.record(
                            to_=receiver_2.address,
                            tickets_to_export=[
                                sp.record(from_=alice.address, amount=1, token_id=0)
                            ],
                        ),
                        sp.record(
                            to_=receiver_1.address,
                            tickets_to_export=[
                                sp.record(from_=alice.address, amount=1, token_id=0)
                            ],
                        ),
                    ],
                    _sender=alice,
                )
                receiver_1.check(
                    vector(
                        ticket_data(fa2.address, 1, (0, None)),
                        ticket_data(fa2.address, 10, (0, None)),
                        ticket_data(fa2.address, 1, (1, None)),
                        ticket_data(fa2.address, 1, (0, None)),
                    )
                )
                sc.verify(receiver_1.data.id == 4)
                receiver_2.check(vector(ticket_data(fa2.address, 1, (0, None))))
                sc.verify(receiver_2.data.id == 1)
                # Sender balance is decreased
                sc.verify(
                    get_balance(fa2, sp.record(owner=alice.address, token_id=0)) == 6
                )
                sc.verify(
                    get_balance(fa2, sp.record(owner=alice.address, token_id=1)) == 40
                )
                # Receiver balance is not increased
                sc.verify(
                    get_balance(fa2, sp.record(owner=receiver_1.address, token_id=0))
                    == 0
                )
                sc.verify(
                    get_balance(fa2, sp.record(owner=receiver_1.address, token_id=1))
                    == 0
                )
                # Total supply doesn't change
                sc.verify(_total_supply(fa2, sp.record(token_id=0)) == 42)

    def test_lambda_export(
        class_, kwargs, ledger_type, version: Version, test_name="", modules=None
    ):
        """Test that the lambda_export entrypoint works as expected.

        Tests:

        - export with insufficient balance
        - export works as expected
        - sandbox address is different than fa2 address.
        - lambda is executed on the sandbox and not on the fa2.
        - sandbox is called with the same amount as received by lambda_export.
        - sandbox is called with the correct list of tickets.
        - sandbox is called with the correct lambda.
        """
        test_name = "test_lambda_export_" + ledger_type + "_" + test_name
        if version != Version.FA2_1:
            raise AttributeError("test_lambda_export only works for FA2.1")
        modules = [] if modules is None else modules
        get_balance = _get_balance_fa2_1

        @sp.add_test()
        def test():
            sc = sp.test_scenario(test_name, modules)
            # Origination is already tested in the `test_core_interfaces` function.
            if sc.simulation_mode() is sp.SimulationMode.MOCKUP:
                return
            sc.add_module(get_helpers_fa2_1())
            sc.h1(test_name)

            sc.h2("Accounts")
            sc.show([admin, alice, bob])

            sc.h2("Sandbox")
            s = get_helpers_fa2_1().Sandbox()
            sc += s
            kwargs["sandbox"] = s.address

            sc.h2("FA2 contract")
            fa2 = class_(**kwargs)
            sc += fa2

            if sc.simulation_mode() is sp.SimulationMode.MOCKUP:
                sc.p("mockups - TODO Ticket in unauthorized position (type error)")
                return

            receiver = get_helpers_fa2_1().Receiver()
            sc += receiver

            m = get_helpers_fa2_1().LambdaMaker()
            sc += m
            lambda_ = sp.View(m, "build_lambda")(
                sp.record(
                    lambda_=get_helpers_fa2_1().lambda_export_ticket,
                    to_=receiver.address,
                )
            )
            # Export with insufficient balance
            sc.h2("Export with insufficient balance")
            alice_balance = get_balance(fa2, sp.record(owner=alice.address, token_id=0))
            sc.verify(alice_balance > 0)
            fa2.lambda_export(
                tickets_to_export=[
                    sp.record(from_=alice.address, amount=alice_balance + 1, token_id=0)
                ],
                action=lambda_,
                _amount=sp.tez(2),
                _sender=alice,
                _valid=False,
                _exception="FA2_INSUFFICIENT_BALANCE",
            )

            token_id = 0 if ledger_type == "SingleAsset" else 1

            if ledger_type == "NFT":
                tickets_to_export = [
                    sp.record(from_=alice.address, amount=1, token_id=0),
                    sp.record(from_=alice.address, amount=1, token_id=1),
                ]
            else:
                tickets_to_export = [
                    sp.record(from_=alice.address, amount=1, token_id=0),
                    sp.record(from_=alice.address, amount=2, token_id=token_id),
                    sp.record(from_=alice.address, amount=1, token_id=token_id),
                ]

            # Export works as expected
            sc.h2("Export works as expected")
            fa2.lambda_export(
                tickets_to_export=tickets_to_export,
                action=lambda_,
                _amount=sp.tez(2),
                _sender=alice,
            )

            sc.verify(receiver.balance == sp.tez(2))
            if ledger_type == "Fungible":
                sc.verify(
                    get_balance(fa2, sp.record(owner=alice.address, token_id=0)) == 41
                )
                sc.verify(
                    get_balance(fa2, sp.record(owner=alice.address, token_id=1)) == 39
                )
            elif ledger_type == "SingleAsset":
                sc.verify(
                    get_balance(fa2, sp.record(owner=alice.address, token_id=0)) == 38
                )
            else:
                sc.verify(
                    get_balance(fa2, sp.record(owner=alice.address, token_id=0)) == 0
                )
                sc.verify(
                    get_balance(fa2, sp.record(owner=alice.address, token_id=1)) == 0
                )

            if ledger_type == "NFT":
                receiver.check(
                    vector(
                        ticket_data(fa2.address, 1, (0, None)),
                        ticket_data(fa2.address, 1, (1, None)),
                    )
                )
            else:
                receiver.check(
                    vector(
                        ticket_data(fa2.address, 1, (0, None)),
                        ticket_data(fa2.address, 2, (token_id, None)),
                        ticket_data(fa2.address, 1, (token_id, None)),
                    )
                )

            # Check that the lambda is executed on the sandbox and not in the FA2 contract
            sc.verify(s.address != fa2.address)
            address_receiver = get_helpers_fa2_1().AddressReceiver()
            sc += address_receiver
            lambda_send_self_address = sp.View(m, "build_lambda")(
                sp.record(
                    lambda_=get_helpers_fa2_1().lambda_send_self_address,
                    to_=address_receiver.address,
                )
            )
            token_id = 2 if ledger_type == "NFT" else token_id
            fa2.lambda_export(
                tickets_to_export=[
                    sp.record(from_=alice.address, amount=1, token_id=token_id),
                ],
                action=lambda_send_self_address,
                _sender=alice,
            )
            sc.verify(address_receiver.data.x.unwrap_some() == s.address)

    def test_import_ticket(
        class_, kwargs, ledger_type, version, test_name="", modules=None
    ):
        """Test that the import_ticket entrypoint works as expected.

        Tests:

        - Import ticket from wrong ticketer
        - Balance is updated
        """
        test_name = "test_import_ticket_" + ledger_type + "_" + test_name
        if version != Version.FA2_1:
            raise AttributeError("test_import_ticket only works for FA2.1")
        modules = [] if modules is None else modules
        get_balance = _get_balance_fa2_1

        @sp.add_test()
        def test():
            sc = sp.test_scenario(test_name, modules)
            # Origination is already tested in the `test_core_interfaces` function.
            if sc.simulation_mode() is sp.SimulationMode.MOCKUP:
                return
            sc.add_module(get_helpers_fa2_1())
            sc.h1(test_name)

            sc.h2("Accounts")
            sc.show([admin, alice, bob])

            sc.h2("Sandbox")
            s = get_helpers_fa2_1().Sandbox()
            sc += s
            kwargs["sandbox"] = s.address

            sc.h2("FA2 contract")
            fa2 = class_(**kwargs)
            sc += fa2

            if sc.simulation_mode() is sp.SimulationMode.MOCKUP:
                sc.p("mockups - cannot compile test ticket")
                return

            sc.h2("Wrong ticketer")
            fa2.import_ticket(
                [
                    sp.record(
                        to_=alice.address,
                        tickets=[sp.test_ticket(alice.address, (0, None), 1)],
                    )
                ],
                _valid=False,
                _exception="FA2.1_INVALID_TICKET",
            )

            token_id = 0 if ledger_type == "SingleAsset" else 1
            amount = 1 if ledger_type == "NFT" else 5

            sc.h2("Import ticket")
            fa2.import_ticket(
                [
                    sp.record(
                        to_=bob.address,
                        tickets=[
                            sp.test_ticket(fa2.address, (0, None), amount),
                            sp.test_ticket(fa2.address, (token_id, None), amount),
                            sp.test_ticket(fa2.address, (0, None), 1),
                        ],
                    ),
                    sp.record(
                        to_=alice.address,
                        tickets=[sp.test_ticket(fa2.address, (0, None), 1)],
                    ),
                    sp.record(
                        to_=alice.address,
                        tickets=[sp.test_ticket(fa2.address, (0, None), 1)],
                    ),
                ],
            )
            if ledger_type == "Fungible":
                sc.verify(
                    get_balance(fa2, sp.record(owner=alice.address, token_id=0)) == 44
                )
                sc.verify(
                    get_balance(fa2, sp.record(owner=bob.address, token_id=0)) == 6
                )
                sc.verify(
                    get_balance(fa2, sp.record(owner=bob.address, token_id=1)) == 5
                )
            elif ledger_type == "SingleAsset":
                sc.verify(
                    get_balance(fa2, sp.record(owner=alice.address, token_id=0)) == 44
                )
                sc.verify(
                    get_balance(fa2, sp.record(owner=bob.address, token_id=0)) == 11
                )
            else:
                sc.verify(
                    get_balance(fa2, sp.record(owner=alice.address, token_id=0)) == 1
                )
                sc.verify(
                    get_balance(fa2, sp.record(owner=bob.address, token_id=0)) == 1
                )


################################################################################

# Optional features tests


class NS:
    """Non standard features of FA2_lib

    Mixin tested:

    - Admin,
    - WithdrawMutez
    - ChangeMetadata
    - OffchainviewTokenMetadata
    - OnchainviewBalanceOf
    - Mint*
    - Burn*
    """

    def test_admin(
        class_, kwargs, ledger_type, test_name="", modules=None, version=Version.FA2
    ):
        """Test `Admin` mixin

        - non admin cannot set admin
        - admin can set admin
        - new admin can set admin
        """
        test_name = "FA2_optional_interfaces_admin" + ledger_type + test_name
        modules = [] if modules is None else modules

        @sp.add_test()
        def test():
            sc = sp.test_scenario(test_name, modules)
            if version == Version.FA2_1:
                sc.add_module(get_helpers_fa2_1())
                sc.h2("Sandbox")
                s = get_helpers_fa2_1().Sandbox()
                sc += s
                kwargs["sandbox"] = s.address

            sc.h2("FA2 contract")
            fa2 = class_(**kwargs)
            sc += fa2
            sc.h1(test_name)
            sc.h2("Non admin cannot set admin")
            fa2.set_administrator(
                alice.address, _sender=alice, _valid=False, _exception="FA2_NOT_ADMIN"
            )
            sc.verify(fa2.data.administrator == admin.address)
            fa2.set_administrator(admin2.address, _sender=admin)
            sc.verify(~(fa2.data.administrator == admin.address))
            sc.verify(fa2.data.administrator == admin2.address)
            fa2.set_administrator(admin.address, _sender=admin2)

    def test_mint(
        class_, kwargs, ledger_type, test_name="", modules=None, version=Version.FA2
    ):
        """Test `Mint*` mixin.

        - `mint` fails with `FA2_NOT_ADMIN` for non-admin.
        - `mint` adds the tokens.
        - `mint` update the supply.
        - `mint` works for existing tokens in fungible contracts.
        """
        test_name = "FA2_mint_" + ledger_type + test_name
        modules = [] if modules is None else modules
        get_balance = _get_balance if version == Version.FA2 else _get_balance_fa2_1

        def mint_nft(sc, fa2):
            sc.h2("Mint entrypoint")
            # Non admin cannot mint a new NFT token.
            sc.h3("NFT mint failure")
            fa2.mint(
                [sp.record(metadata=tok0_md, to_=alice.address)],
                _sender=alice,
                _valid=False,
                _exception="FA2_NOT_ADMIN",
            )

            sc.h3("Mint")
            # Mint of a new NFT token.
            fa2.mint(
                [
                    sp.record(metadata=tok0_md, to_=alice.address),
                    sp.record(metadata=tok1_md, to_=alice.address),
                    sp.record(metadata=tok2_md, to_=bob.address),
                ],
                _sender=admin,
            )

            # Check that the balance is updated.
            sc.verify(get_balance(fa2, sp.record(owner=alice.address, token_id=0)) == 1)
            sc.verify(get_balance(fa2, sp.record(owner=bob.address, token_id=0)) == 0)
            sc.verify(get_balance(fa2, sp.record(owner=alice.address, token_id=1)) == 1)
            sc.verify(get_balance(fa2, sp.record(owner=bob.address, token_id=1)) == 0)
            sc.verify(get_balance(fa2, sp.record(owner=alice.address, token_id=2)) == 0)
            sc.verify(get_balance(fa2, sp.record(owner=bob.address, token_id=2)) == 1)

            # Check that the supply is updated.
            sc.verify(_total_supply(fa2, sp.record(token_id=0)) == 1)
            sc.verify(_total_supply(fa2, sp.record(token_id=1)) == 1)
            sc.verify(_total_supply(fa2, sp.record(token_id=2)) == 1)

        def mint_fungible(sc, fa2):
            sc.h2("Mint entrypoint")
            # Non admin cannot mint a new fungible token.
            sc.h3("Fungible mint failure")
            fa2.mint(
                [
                    sp.record(
                        token=sp.variant.new(tok0_md), to_=alice.address, amount=1000
                    )
                ],
                _sender=alice,
                _valid=False,
                _exception="FA2_NOT_ADMIN",
            )

            sc.h3("Mint")
            # Mint of a new fungible token.
            fa2.mint(
                [
                    sp.record(
                        token=sp.variant.new(tok0_md), to_=alice.address, amount=1000
                    )
                ],
                _sender=admin,
            )

            # Check ledger update.
            sc.verify(
                get_balance(fa2, sp.record(owner=alice.address, token_id=0)) == 1000
            )
            sc.verify(get_balance(fa2, sp.record(owner=bob.address, token_id=0)) == 0)
            # Check supply update.
            sc.verify(_total_supply(fa2, sp.record(token_id=0)) == 1000)

            # Mint a new and existing token.
            fa2.mint(
                [
                    sp.record(
                        token=sp.variant.new(tok1_md), to_=alice.address, amount=1000
                    ),
                    sp.record(
                        token=sp.variant.existing(0), to_=alice.address, amount=1000
                    ),
                    sp.record(
                        token=sp.variant.existing(1), to_=bob.address, amount=1000
                    ),
                ],
                _sender=admin,
            )

            # Check ledger update.
            sc.verify(
                get_balance(fa2, sp.record(owner=alice.address, token_id=0)) == 2000
            )
            sc.verify(get_balance(fa2, sp.record(owner=bob.address, token_id=0)) == 0)
            sc.verify(
                get_balance(fa2, sp.record(owner=alice.address, token_id=1)) == 1000
            )
            sc.verify(
                get_balance(fa2, sp.record(owner=bob.address, token_id=1)) == 1000
            )
            # Check supply update.
            sc.verify(_total_supply(fa2, sp.record(token_id=0)) == 2000)
            sc.verify(_total_supply(fa2, sp.record(token_id=1)) == 2000)

        def mint_single_asset(sc, fa2):
            sc.h2("Mint entrypoint")
            # Non admin cannot mint a new fungible token.
            sc.h3("Single asset mint failure")
            fa2.mint(
                [sp.record(to_=alice.address, amount=1000)],
                _sender=alice,
                _valid=False,
                _exception="FA2_NOT_ADMIN",
            )

            sc.h3("Mint")
            # Mint some tokens
            fa2.mint([sp.record(to_=alice.address, amount=1000)], _sender=admin)

            # Check ledger update.
            sc.verify(
                get_balance(fa2, sp.record(owner=alice.address, token_id=0)) == 1000
            )
            sc.verify(get_balance(fa2, sp.record(owner=bob.address, token_id=0)) == 0)
            # Check supply update.
            sc.verify(_total_supply(fa2, sp.record(token_id=0)) == 1000)

            # multiple mint
            fa2.mint(
                [
                    sp.record(to_=alice.address, amount=1000),
                    sp.record(to_=bob.address, amount=1000),
                    sp.record(to_=bob.address, amount=1000),
                ],
                _sender=admin,
            )

            # Check ledger update.
            sc.verify(
                get_balance(fa2, sp.record(owner=alice.address, token_id=0)) == 2000
            )
            sc.verify(
                get_balance(fa2, sp.record(owner=bob.address, token_id=0)) == 2000
            )
            # Check supply update.
            sc.verify(_total_supply(fa2, sp.record(token_id=0)) == 4000)

        @sp.add_test()
        def test():
            sc = sp.test_scenario(test_name, modules)
            if version == Version.FA2_1:
                sc.add_module(get_helpers_fa2_1())
                sc.h2("Sandbox")
                s = get_helpers_fa2_1().Sandbox()
                sc += s
                kwargs["sandbox"] = s.address
            fa2 = class_(**kwargs)
            sc += fa2
            sc.h1(test_name)
            if sc.simulation_mode() is sp.SimulationMode.MOCKUP:
                sc.p("mockups - fix transfer based testing")
                return

            if ledger_type == "NFT":
                mint_nft(sc, fa2)
            elif ledger_type == "Fungible":
                mint_fungible(sc, fa2)
            elif ledger_type == "SingleAsset":
                mint_single_asset(sc, fa2)
            else:
                raise Exception(
                    'fa2.ledger type must be "NFT", "Fungible" or "SingleAsset".'
                )

    def test_burn(
        class_,
        kwargs,
        ledger_type,
        supports_transfer,
        supports_operator,
        modules=None,
        test_name="",
        version=Version.FA2,
    ):
        """Test `Burn*` mixin.

        - non operator cannot burn, it fails appropriately.
        - owner can burn.
        - operator can burn if the policy allows it.
        """
        test_name = "FA2_burn_" + ledger_type + test_name
        modules = [] if modules is None else modules
        get_balance = _get_balance if version == Version.FA2 else _get_balance_fa2_1

        @sp.add_test()
        def test():
            amount = 1 if ledger_type == "NFT" else 20
            sc = sp.test_scenario(test_name, modules)
            if version == Version.FA2_1:
                sc.add_module(get_helpers_fa2_1())
                sc.h2("Sandbox")
                s = get_helpers_fa2_1().Sandbox()
                sc += s
                kwargs["sandbox"] = s.address
            fa2 = class_(**kwargs)
            sc += fa2
            sc.h1(test_name)
            sc.h2("Burn entrypoint")

            # Check that non operator cannot burn others tokens.
            sc.h3("Cannot burn others tokens")
            exception = (
                (
                    ("FA2_NOT_OPERATOR", "FA2.1_INSUFFICIENT_ALLOWANCE")
                    if version == Version.FA2_1
                    else "FA2_NOT_OPERATOR"
                )
                if supports_transfer
                else "FA2_TX_DENIED"
            )
            fa2.burn(
                [sp.record(token_id=0, from_=alice.address, amount=1)],
                _sender=bob,
                _valid=False,
                _exception=exception,
            )

            # Not allowed transfers
            if not supports_transfer:
                fa2.burn(
                    [sp.record(token_id=0, from_=alice.address, amount=amount)],
                    _sender=alice,
                    _valid=False,
                    _exception="FA2_TX_DENIED",
                )
                return

            if sc.simulation_mode() is sp.SimulationMode.MOCKUP:
                sc.p("mockups - fix transfer based testing")
                return

            # Owner can burn.
            sc.h3("Owner burns his nft tokens")
            fa2.burn(
                [sp.record(token_id=0, from_=alice.address, amount=amount)],
                _sender=alice,
            )

            if ledger_type == "NFT":
                # Check that the contract storage is updated.
                sc.verify(~fa2.data.ledger.contains(0))
                # Check that burning an nft removes token_metadata.
                sc.verify(~fa2.data.token_metadata.contains(0))
            else:
                # Check ledger update.
                sc.verify(
                    get_balance(fa2, sp.record(owner=alice.address, token_id=0)) == 22
                )
                # Check that burning doesn't remove token_metadata.
                sc.verify(fa2.data.token_metadata.contains(0))
                # Check supply update.
                sc.verify(_total_supply(fa2, sp.record(token_id=0)) == 22)

            token_id = 0 if ledger_type == "SingleAsset" else 1
            if supports_operator:
                # Add operator to test if he can burn on behalf of the owner.
                sc.h3("Operator can burn on behalf of the owner")
                operator_bob = sp.record(
                    owner=alice.address, operator=bob.address, token_id=token_id
                )
                fa2.update_operators(
                    [sp.variant.add_operator(operator_bob)], _sender=alice
                )
                # Operator can burn nft on behalf of the owner.
                fa2.burn(
                    [sp.record(token_id=token_id, from_=alice.address, amount=0)],
                    _sender=bob,
                )

    def test_withdraw_mutez(
        class_, kwargs, ledger_type, test_name="", modules=None, version=Version.FA2
    ):
        """Test of WithdrawMutez.

        - non admin cannot withdraw mutez: FA2_NOT_ADMIN.
        - admin can withdraw mutez.
        """
        test_name = "FA2_withdraw_mutez" + ledger_type + test_name
        modules = [] if modules is None else modules
        get_balance = _get_balance if version == Version.FA2 else _get_balance_fa2_1

        @sp.add_test()
        def test():
            sc = sp.test_scenario(test_name, modules)
            if version == Version.FA2_1:
                sc.add_module(get_helpers_fa2_1())
                sc.h2("Sandbox")
                s = get_helpers_fa2_1().Sandbox()
                sc += s
                kwargs["sandbox"] = s.address
            sc.add_module(helpers)
            fa2 = class_(**kwargs)
            sc += fa2
            sc.h1(test_name)
            sc.h2("Mutez receiver contract")

            wallet = helpers.Wallet()
            sc += wallet

            # Non admin cannot withdraw mutez.
            sc.h2("Non admin cannot withdraw_mutez")
            fa2.withdraw_mutez(
                destination=wallet.address,
                amount=sp.tez(10),
                _sender=alice,
                _amount=sp.tez(42),
                _valid=False,
                _exception="FA2_NOT_ADMIN",
            )

            if sc.simulation_mode() is sp.SimulationMode.MOCKUP:
                sc.p("mockups - fix transfer based testing")
                return

            # Admin can withdraw mutez.
            sc.h3("Admin withdraw_mutez")
            fa2.withdraw_mutez(
                destination=wallet.address,
                amount=sp.tez(10),
                _sender=admin,
                _amount=sp.tez(42),
            )

            # Check that the mutez has been transferred.
            sc.verify(fa2.balance == sp.tez(32))
            sc.verify(wallet.balance == sp.tez(10))

    def test_change_metadata(
        class_, kwargs, ledger_type, test_name="", modules=None, version=Version.FA2
    ):
        """Test of ChangeMetadata.

        - non admin cannot set metadata
        - `set_metadata` works as expected
        """
        test_name = "FA2_change_metadata" + ledger_type + test_name
        modules = [] if modules is None else modules
        get_balance = _get_balance if version == Version.FA2 else _get_balance_fa2_1

        @sp.add_test()
        def test():
            sc = sp.test_scenario(test_name, modules)
            if version == Version.FA2_1:
                sc.add_module(get_helpers_fa2_1())
                sc.h2("Sandbox")
                s = get_helpers_fa2_1().Sandbox()
                sc += s
                kwargs["sandbox"] = s.address
            fa2 = class_(**kwargs)
            sc += fa2
            sc.h1(test_name)
            sc.h2("Change metadata")
            sc.h3("Non admin cannot set metadata")
            fa2.set_metadata(
                sp.scenario_utils.metadata_of_url("http://example.com"),
                _sender=alice,
                _valid=False,
                _exception="FA2_NOT_ADMIN",
            )

            sc.h3("Admin set metadata")
            fa2.set_metadata(
                sp.scenario_utils.metadata_of_url("http://example.com"), _sender=admin
            )

            if sc.simulation_mode() is sp.SimulationMode.MOCKUP:
                sc.p("mockups - TODO fix admin metadata change test to not use a url")
                return

            # Check that the metadata has been updated.
            sc.verify_equal(
                fa2.data.metadata[""],
                sp.scenario_utils.metadata_of_url("http://example.com")[""],
            )

    def test_get_balance_of(
        class_, kwargs, ledger_type, test_name="", modules=None, version=Version.FA2
    ):
        """Test of `OnchainviewBalanceOf`

        - `get_balance_of` doesn't deduplicate nor reorder on nft.
        - `get_balance_of` doesn't deduplicate nor reorder on fungible.
        - `get_balance_of` fails with `FA2_TOKEN_UNDEFINED` when needed on nft.
        - `get_balance_of` fails with `FA2_TOKEN_UNDEFINED` when needed on fungible.
        """
        test_name = "FA2_get_balance_of" + ledger_type + test_name
        modules = [] if modules is None else modules
        get_balance = _get_balance if version == Version.FA2 else _get_balance_fa2_1

        @sp.add_test()
        def test():
            sc = sp.test_scenario(test_name, modules)
            if version == Version.FA2_1:
                sc.add_module(get_helpers_fa2_1())
                sc.h2("Sandbox")
                s = get_helpers_fa2_1().Sandbox()
                sc += s
                kwargs["sandbox"] = s.address
            fa2 = class_(**kwargs)
            sc += fa2
            sc.h1(test_name)

            # get_balance_of on fungible
            # We deliberately give multiple identical params to check for
            # non-deduplication and non-reordering.

            ICO = 1 if ledger_type == "NFT" else 42  # Initial coin offering.
            last_token_id = 0 if ledger_type == "SingleAsset" else 2

            requests = [
                sp.record(owner=alice.address, token_id=0),
                sp.record(owner=alice.address, token_id=0),
                sp.record(owner=bob.address, token_id=0),
                sp.record(owner=alice.address, token_id=last_token_id),
            ]
            expected = [
                sp.record(
                    balance=ICO, request=sp.record(owner=alice.address, token_id=0)
                ),
                sp.record(
                    balance=ICO, request=sp.record(owner=alice.address, token_id=0)
                ),
                sp.record(balance=0, request=sp.record(owner=bob.address, token_id=0)),
                sp.record(
                    balance=ICO,
                    request=sp.record(owner=alice.address, token_id=last_token_id),
                ),
            ]

            if sc.simulation_mode() is sp.SimulationMode.MOCKUP:
                sc.p("mockups - fix transfer based testing")
                return

            sc.verify_equal(_get_balance_of(fa2, requests), expected)

            # Check that on-chain view fails on undefined tokens.
            sc.verify(
                sp.catch_exception(
                    _get_balance_of(fa2, [sp.record(owner=alice.address, token_id=5)])
                )
                == sp.Some("FA2_TOKEN_UNDEFINED")
            )

    def test_offchain_token_metadata(
        class_, kwargs, ledger_type, test_name="", modules=None, version=Version.FA2
    ):
        """Test `OffchainviewTokenMetadata`.

        Tests:

        - `token_metadata` works as expected on nft and fungible.
        """
        test_name = "FA2_offchain_token_metadata" + ledger_type + test_name
        modules = [] if modules is None else modules
        get_balance = _get_balance if version == Version.FA2 else _get_balance_fa2_1

        @sp.add_test()
        def test():
            sc = sp.test_scenario(test_name, modules)
            if version == Version.FA2_1:
                sc.add_module(get_helpers_fa2_1())
                sc.h2("Sandbox")
                s = get_helpers_fa2_1().Sandbox()
                sc += s
                kwargs["sandbox"] = s.address
            fa2 = class_(**kwargs)
            sc += fa2
            sc.h1(test_name)
            sc.verify_equal(
                fa2.token_metadata(0), sp.record(token_id=0, token_info=tok0_md)
            )

    def test_pause(
        class_, kwargs, ledger_type, test_name="", modules=None, version=Version.FA2
    ):
        """Test the `Pause` policy decorator.

        - transfer works without pause
        - transfer update_operators without pause
        - non admin cannot set_pause
        - admin can set pause
        - transfer fails with ('FA2_TX_DENIED', 'FA2_PAUSED') when paused.
        - update_operators fails with
        ('FA2_OPERATORS_UNSUPPORTED', 'FA2_PAUSED') when paused.
        """
        test_name = "FA2_pause_" + ledger_type + test_name
        modules = [] if modules is None else modules
        get_balance = _get_balance if version == Version.FA2 else _get_balance_fa2_1

        @sp.add_test()
        def test():
            sc = sp.test_scenario(test_name, modules)
            if version == Version.FA2_1:
                sc.add_module(get_helpers_fa2_1())
                sc.h2("Sandbox")
                s = get_helpers_fa2_1().Sandbox()
                sc += s
                kwargs["sandbox"] = s.address
            fa2 = class_(**kwargs)
            sc.h1(test_name)

            sc.h2("Accounts")
            sc.show([admin, alice, bob])
            sc.h2("FA2 Contract")
            sc += fa2

            sc.h2("Transfer without pause")
            fa2.transfer(
                [
                    sp.record(
                        from_=alice.address,
                        txs=[sp.record(to_=alice.address, amount=0, token_id=0)],
                    ),
                ],
                _sender=alice,
            )

            sc.h2("Update_operator without pause")
            fa2.update_operators(
                [
                    sp.variant(
                        "add_operator",
                        sp.record(
                            owner=alice.address, operator=alice.address, token_id=0
                        ),
                    ),
                    sp.variant(
                        "remove_operator",
                        sp.record(
                            owner=alice.address, operator=alice.address, token_id=0
                        ),
                    ),
                ],
                _sender=alice,
            )

            sc.h2("Pause entrypoint")
            sc.h3("Non admin cannot set pause")
            fa2.set_pause(True, _sender=alice, _valid=False, _exception="FA2_NOT_ADMIN")

            sc.h3("Admin set pause")
            fa2.set_pause(True, _sender=admin)

            sc.h2("Transfer fails with pause")
            fa2.transfer(
                [
                    sp.record(
                        from_=alice.address,
                        txs=[sp.record(to_=alice.address, amount=0, token_id=0)],
                    ),
                ],
                _sender=alice,
                _valid=False,
                _exception=("FA2_TX_DENIED", "FA2_PAUSED"),
            )

            sc.h2("Update_operator fails with pause")
            fa2.update_operators(
                [
                    sp.variant(
                        "add_operator",
                        sp.record(
                            owner=alice.address, operator=alice.address, token_id=0
                        ),
                    ),
                    sp.variant(
                        "remove_operator",
                        sp.record(
                            owner=alice.address, operator=alice.address, token_id=0
                        ),
                    ),
                ],
                _sender=alice,
                _valid=False,
                _exception=("FA2_OPERATORS_UNSUPPORTED", "FA2_PAUSED"),
            )
