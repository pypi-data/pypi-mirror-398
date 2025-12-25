import smartpy as sp


@sp.module
def main():
    class TestCheckSignature(sp.Contract):
        def __init__(self, boss_pk):
            self.data.currentValue = "Hello World"
            self.data.counter = 0
            self.data.bossPublicKey = boss_pk

        @sp.entrypoint
        def setCurrentValue(self, params):
            # We will also need Michelson SELF and CHAIN_ID to avoid all replay attacks:
            thingToSign = sp.pack(
                sp.record(
                    o=self.data.currentValue, n=params.newValue, c=self.data.counter
                )
            )
            assert sp.check_signature(
                self.data.bossPublicKey, params.userSignature, thingToSign
            )
            self.data.currentValue = params.newValue
            self.data.counter = self.data.counter + 1


@sp.add_test()
def test():
    scenario = sp.test_scenario("CheckSignature")
    scenario.h1("Check Signature")
    rightful_owner = sp.test_account("Alice")
    attacker = sp.test_account("Robert")
    c1 = main.TestCheckSignature(rightful_owner.public_key)

    scenario += c1
    if scenario.simulation_mode() is sp.SimulationMode.MOCKUP:
        scenario.p("mockup mode doesnt support secret keys as params")
        return

    # Let's build a successful call:
    #
    scenario.h2("Successful Call")
    first_message_packed = sp.pack(sp.record(o="Hello World", n="should work", c=0))
    sig_from_alice = sp.make_signature(
        secret_key=rightful_owner.secret_key,
        message=first_message_packed,
        message_format="Raw",
    )
    c1.setCurrentValue(
        newValue="should work", userSignature=sig_from_alice, _valid=True
    )
    #
    scenario.h2("Replay Attack")
    scenario.p(
        "Trying to reuse the same signature is blocked by the value of the counter."
    )
    c1.setCurrentValue(
        newValue="should work", userSignature=sig_from_alice, _valid=False
    )
    #
    #
    scenario.h2("Signature From Wrong Secret Key")
    scenario.p("Signing the right thing from a different secret-key.")
    #
    #
    # Gives:
    second_message_packed = sp.pack(
        sp.record(o="should work", n="Hello again World", c=1)
    )
    sig_from_bob = sp.make_signature(
        secret_key=attacker.secret_key,
        message=second_message_packed,
        message_format="Raw",
    )
    c1.setCurrentValue(
        newValue="Hello again World", userSignature=sig_from_bob, _valid=False
    )
    #
    scenario.h2("Second Successful Call")
    scenario.p(
        "Showing that the previous call failed <b>because</b> of the secret-key (signing same bytes)."
    )
    sig_from_alice = sp.make_signature(
        secret_key=rightful_owner.secret_key,
        message=second_message_packed,
        message_format="Raw",
    )
    c1.setCurrentValue(
        newValue="Hello again World", userSignature=sig_from_alice, _valid=True
    )
