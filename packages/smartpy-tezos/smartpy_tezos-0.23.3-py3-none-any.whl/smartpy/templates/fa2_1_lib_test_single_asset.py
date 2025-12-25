import smartpy as sp
from smartpy.templates import fa2_1_lib as fa2
from smartpy.templates import fa2_lib_testing as testing
from smartpy.templates import fa2_types

administrator = sp.test_account("Administrator")
alice = sp.test_account("Alice")
tok0_md = fa2.make_metadata(name="Token Zero", decimals=1, symbol="Tok0")
METADATA = sp.scenario_utils.metadata_of_url("ipfs://example")

main = fa2.main


@sp.module
def m():
    import main

    # Order of inheritance: [Admin], [<policy>], <base class>, [<mixins>]

    class SingleAssetTestNoTransfer(main.NoTransfer, main.SingleAsset):
        def __init__(self, metadata, ledger, token_metadata, sandbox):
            main.SingleAsset.__init__(self, metadata, ledger, token_metadata, sandbox)
            main.NoTransfer.__init__(self)

    class SingleAssetTestOwnerTransfer(main.OwnerTransfer, main.SingleAsset):
        def __init__(self, metadata, ledger, token_metadata, sandbox):
            main.SingleAsset.__init__(self, metadata, ledger, token_metadata, sandbox)
            main.OwnerTransfer.__init__(self)

    class SingleAssetTestFull(
        main.Admin,
        main.SingleAsset,
        main.ChangeMetadata,
        main.WithdrawMutez,
        main.MintSingleAsset,
        main.BurnSingleAsset,
        main.OffchainviewTokenMetadata,
        main.OnchainviewBalanceOf,
    ):
        def __init__(self, administrator, metadata, ledger, token_metadata, sandbox):
            main.OnchainviewBalanceOf.__init__(self)
            main.OffchainviewTokenMetadata.__init__(self)
            main.BurnSingleAsset.__init__(self)
            main.MintSingleAsset.__init__(self)
            main.WithdrawMutez.__init__(self)
            main.ChangeMetadata.__init__(self)
            main.SingleAsset.__init__(self, metadata, ledger, token_metadata, sandbox)
            main.Admin.__init__(self, administrator)


if "main" in __name__:
    ledger = {(alice.address): 42}
    token_metadata = tok0_md

    # Default SingleAsset
    c1 = [
        m.SingleAssetTestFull,
        {
            "administrator": administrator.address,
            "metadata": METADATA,
            "ledger": ledger,
            "token_metadata": token_metadata,
        },
    ]

    # No transfer
    c2 = [
        m.SingleAssetTestNoTransfer,
        {
            "metadata": METADATA,
            "ledger": ledger,
            "token_metadata": token_metadata,
        },
    ]

    # Owner transfer
    c3 = [
        m.SingleAssetTestOwnerTransfer,
        {
            "metadata": METADATA,
            "ledger": ledger,
            "token_metadata": token_metadata,
        },
    ]

    # Empty SingleAsset
    c4 = [
        m.SingleAssetTestFull,
        {
            "administrator": administrator.address,
            "metadata": METADATA,
            "ledger": {},
            "token_metadata": token_metadata,
        },
    ]

    kwargs = {
        "modules": [fa2_types.t, fa2.main, m],
        "ledger_type": "SingleAsset",
        "version": testing.Version.FA2_1,
    }

    # Standard features
    testing.test_core_interfaces(*c1, **kwargs)
    testing.test_transfer(*c1, **kwargs)
    testing.test_balance_of(*c1, **kwargs)
    # Policies
    testing.test_owner_or_operator_transfer(*c1, **kwargs)
    testing.test_no_transfer(*c2, **kwargs)
    testing.test_owner_transfer(*c3, **kwargs)

    # # FA2.1 specific features
    testing.Fa2_1.test_approve(*c1, **kwargs)
    testing.Fa2_1.test_approve_only_owner(*c1, **kwargs)
    testing.Fa2_1.test_transfer_allowance(*c1, **kwargs)
    testing.Fa2_1.test_export_ticket(*c1, **kwargs)
    testing.Fa2_1.test_lambda_export(*c1, **kwargs)
    testing.Fa2_1.test_import_ticket(*c1, **kwargs)

    # Non standard features
    testing.NS.test_admin(*c1, **kwargs)
    testing.NS.test_mint(*c4, **kwargs)
    testing.NS.test_burn(*c1, supports_transfer=True, supports_operator=True, **kwargs)
    testing.NS.test_withdraw_mutez(*c1, **kwargs)
    testing.NS.test_change_metadata(*c1, **kwargs)
    testing.NS.test_get_balance_of(*c1, **kwargs)
