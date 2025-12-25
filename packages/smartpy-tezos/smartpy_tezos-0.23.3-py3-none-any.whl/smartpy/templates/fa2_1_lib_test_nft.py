import smartpy as sp
from smartpy.templates import fa2_1_lib as fa2
from smartpy.templates import fa2_lib_testing as testing
from smartpy.templates import fa2_types

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

    class NftTestNoTransfer(main.NoTransfer, main.Nft):
        def __init__(self, metadata, ledger, token_metadata, sandbox):
            main.Nft.__init__(self, metadata, ledger, token_metadata, sandbox)
            main.NoTransfer.__init__(self)

    class NftTestOwnerTransfer(main.OwnerTransfer, main.Nft):
        def __init__(self, metadata, ledger, token_metadata, sandbox):
            main.Nft.__init__(self, metadata, ledger, token_metadata, sandbox)
            main.OwnerTransfer.__init__(self)

    class NftTestFull(
        main.Admin,
        main.Nft,
        main.ChangeMetadata,
        main.WithdrawMutez,
        main.MintNft,
        main.BurnNft,
        main.OffchainviewTokenMetadata,
        main.OnchainviewBalanceOf,
    ):
        def __init__(self, administrator, metadata, ledger, token_metadata, sandbox):
            main.OnchainviewBalanceOf.__init__(self)
            main.OffchainviewTokenMetadata.__init__(self)
            main.BurnNft.__init__(self)
            main.MintNft.__init__(self)
            main.WithdrawMutez.__init__(self)
            main.ChangeMetadata.__init__(self)
            main.Nft.__init__(self, metadata, ledger, token_metadata, sandbox)
            main.Admin.__init__(self, administrator)


if "main" in __name__:
    ledger = {
        0: alice.address,
        1: alice.address,
        2: alice.address,
    }
    token_metadata = TOKEN_METADATA

    # Default Nft
    c1 = [
        m.NftTestFull,
        {
            "administrator": administrator.address,
            "metadata": METADATA,
            "ledger": ledger,
            "token_metadata": token_metadata,
        },
    ]

    # No transfer
    c2 = [
        m.NftTestNoTransfer,
        {
            "metadata": METADATA,
            "ledger": ledger,
            "token_metadata": token_metadata,
        },
    ]

    # Owner transfer
    c3 = [
        m.NftTestOwnerTransfer,
        {
            "metadata": METADATA,
            "ledger": ledger,
            "token_metadata": token_metadata,
        },
    ]

    # Empty Nft
    c4 = [
        m.NftTestFull,
        {
            "administrator": administrator.address,
            "metadata": METADATA,
            "ledger": {},
            "token_metadata": [],
        },
    ]

    kwargs = {
        "modules": [fa2_types.t, fa2.main, m],
        "ledger_type": "NFT",
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
    # testing.Fa2_1.test_export_ticket(*c1, **kwargs)
    testing.Fa2_1.test_lambda_export(*c1, **kwargs)
    # testing.Fa2_1.test_import_ticket(*c1, **kwargs)

    # Non standard features
    testing.NS.test_admin(*c1, **kwargs)
    testing.NS.test_mint(*c4, **kwargs)
    testing.NS.test_burn(*c1, supports_transfer=True, supports_operator=True, **kwargs)
    testing.NS.test_withdraw_mutez(*c1, **kwargs)
    testing.NS.test_change_metadata(*c1, **kwargs)
    testing.NS.test_get_balance_of(*c1, **kwargs)
