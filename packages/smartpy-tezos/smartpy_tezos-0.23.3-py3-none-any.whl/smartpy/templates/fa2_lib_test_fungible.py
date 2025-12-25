import smartpy as sp
from fa2_lib import fa2_lib as fa2
from fa2_lib import fa2_lib_testing as testing

administrator = sp.test_account("Administrator")
alice = sp.test_account("Alice")
tok0_md = fa2.make_metadata(name="Token Zero", decimals=1, symbol="Tok0")
tok1_md = fa2.make_metadata(name="Token One", decimals=1, symbol="Tok1")
tok2_md = fa2.make_metadata(name="Token Two", decimals=1, symbol="Tok2")
TOKEN_METADATA = [tok0_md, tok1_md, tok2_md]
METADATA = sp.scenario_utils.metadata_of_url("ipfs://example")

main = fa2.main


@sp.module
def m():
    import main

    # Order of inheritance: [Admin], [<policy>], <base class>, [<mixins>]

    class FungibleTestNoTransfer(main.NoTransfer, main.Fungible):
        def __init__(self, metadata, ledger, token_metadata):
            main.Fungible.__init__(self, metadata, ledger, token_metadata)
            main.NoTransfer.__init__(self)

    class FungibleTestOwnerTransfer(main.OwnerTransfer, main.Fungible):
        def __init__(self, metadata, ledger, token_metadata):
            main.Fungible.__init__(self, metadata, ledger, token_metadata)
            main.OwnerTransfer.__init__(self)

    class FungibleTestPauseOwnerOrOperatorTransfer(
        main.Admin, main.PauseOwnerOrOperatorTransfer, main.Fungible
    ):
        def __init__(self, administrator, metadata, ledger, token_metadata):
            main.Fungible.__init__(self, metadata, ledger, token_metadata)
            main.PauseOwnerOrOperatorTransfer.__init__(self)
            main.Admin.__init__(self, administrator)

    class FungibleTestFull(
        main.Admin,
        main.Fungible,
        main.ChangeMetadata,
        main.WithdrawMutez,
        main.MintFungible,
        main.BurnFungible,
        main.OffchainviewTokenMetadata,
        main.OnchainviewBalanceOf,
    ):
        def __init__(self, administrator, metadata, ledger, token_metadata):
            main.OnchainviewBalanceOf.__init__(self)
            main.OffchainviewTokenMetadata.__init__(self)
            main.BurnFungible.__init__(self)
            main.MintFungible.__init__(self)
            main.WithdrawMutez.__init__(self)
            main.ChangeMetadata.__init__(self)
            main.Fungible.__init__(self, metadata, ledger, token_metadata)
            main.Admin.__init__(self, administrator)


if "main" in __name__:
    ledger = {
        (alice.address, 0): 42,
        (alice.address, 1): 42,
        (alice.address, 2): 42,
    }
    token_metadata = TOKEN_METADATA

    # Default Fungible
    c1 = [
        m.FungibleTestFull,
        {
            "administrator": administrator.address,
            "metadata": METADATA,
            "ledger": ledger,
            "token_metadata": token_metadata,
        },
    ]

    # No transfer
    c2 = [
        m.FungibleTestNoTransfer,
        {
            "metadata": METADATA,
            "ledger": ledger,
            "token_metadata": token_metadata,
        },
    ]

    # Owner transfer
    c3 = [
        m.FungibleTestOwnerTransfer,
        {
            "metadata": METADATA,
            "ledger": ledger,
            "token_metadata": token_metadata,
        },
    ]

    # Empty Fungible
    c4 = [
        m.FungibleTestFull,
        {
            "administrator": administrator.address,
            "metadata": METADATA,
            "ledger": {},
            "token_metadata": [],
        },
    ]

    # Pause owner or operator transfer
    c5 = [
        m.FungibleTestPauseOwnerOrOperatorTransfer,
        {
            "administrator": administrator.address,
            "metadata": METADATA,
            "ledger": ledger,
            "token_metadata": token_metadata,
        },
    ]

    kwargs = {"modules": [m], "ledger_type": "Fungible"}

    # Standard features
    testing.test_core_interfaces(*c1, **kwargs)
    testing.test_transfer(*c1, **kwargs)
    testing.test_balance_of(*c1, **kwargs)
    # Policies
    testing.test_owner_or_operator_transfer(*c1, **kwargs)
    testing.test_no_transfer(*c2, **kwargs)
    testing.test_owner_transfer(*c3, **kwargs)

    # Non standard features
    testing.NS.test_admin(*c1, **kwargs)
    testing.NS.test_mint(*c4, **kwargs)
    testing.NS.test_burn(*c1, supports_transfer=True, supports_operator=True, **kwargs)
    testing.NS.test_withdraw_mutez(*c1, **kwargs)
    testing.NS.test_change_metadata(*c1, **kwargs)
    testing.NS.test_get_balance_of(*c1, **kwargs)
    # Non standard policies
    testing.NS.test_pause(*c5, **kwargs)
