import smartpy as sp


@sp.module
def main():
    class Receiver(sp.Contract):
        @sp.entrypoint
        def receive_and_check(self, sender_balance, receiver_balance):
            assert (
                sender_balance
                == sp.view("get_balance", sp.sender, (), sp.mutez).unwrap_some()
            )
            assert receiver_balance == sp.balance

    class Sender(sp.Contract):
        @sp.entrypoint
        def send(self, a):
            c = sp.contract(
                sp.record(sender_balance=sp.mutez, receiver_balance=sp.mutez),
                a,
                entrypoint="receive_and_check",
            ).unwrap_some()
            sp.transfer(
                sp.record(sender_balance=sp.tez(110), receiver_balance=sp.tez(1)),
                sp.tez(1),
                c,
            )
            sp.transfer(
                sp.record(sender_balance=sp.tez(100), receiver_balance=sp.tez(11)),
                sp.tez(10),
                c,
            )

        @sp.onchain_view()
        def get_balance(self):
            return sp.balance


if "main" in __name__:

    @sp.add_test()
    def test():
        sc = sp.test_scenario("Test")

        sender = main.Sender()
        sender.set_initial_balance(sp.tez(111))
        sc += sender

        receiver = main.Receiver()
        sc += receiver

        sender.send(receiver.address)
