import smartpy as sp


@sp.module
def main():
    class ChainId(sp.Contract):
        def __init__(self):
            self.data.chainId = None

        @sp.entrypoint
        def test(self):
            self.data.chainId = sp.Some(sp.chain_id)


@sp.add_test()
def chainIdTest():
    scenario = sp.test_scenario("ChainId")
    c = main.ChainId()
    scenario += c
    c.test(_chain_id=sp.chain_id_cst("0x9caecab8"))
