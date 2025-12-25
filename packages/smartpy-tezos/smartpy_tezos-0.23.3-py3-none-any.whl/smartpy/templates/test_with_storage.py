import smartpy as sp


@sp.module
def main():
    f_type: type = sp.lambda_(sp.nat, sp.nat, with_storage="read-write")

    @sp.effects(with_storage="read-write")
    def set_f(x):
        sp.cast(x, sp.nat)
        self.data.x = x
        return x * 100

    class Library(sp.Contract):
        def __init__(self):
            self.data.x = 0

        @sp.onchain_view()
        def get_set_f(self):
            return set_f

    # Same as Library, but different storage.
    class Library2(sp.Contract):
        def __init__(self):
            self.data.y = "abc"

        @sp.onchain_view()
        def get_set_f(self):
            return set_f

    class Main(sp.Contract):
        def __init__(self):
            self.data.x = 0

        @sp.entrypoint
        def run(self, f: f_type, x):
            _ = f(x)

        @sp.entrypoint
        def save(self, f, x):
            sp.cast(f, f_type)
            self.data.x = f(x)

    class Remote(sp.Contract):
        @sp.entrypoint
        def call(self, lib, main, x):
            remote_set_f = sp.view("get_set_f", lib, (), f_type).unwrap_some()
            main_run = sp.contract(
                sp.record(f=f_type, x=sp.nat), main, entrypoint="run"
            ).unwrap_some()
            sp.transfer(sp.record(f=remote_set_f, x=x), sp.mutez(0), main_run)

    @sp.effects(with_storage="read-write")
    def f(x) -> sp.nat:
        sp.cast(self.data, sp.record(x=sp.nat))
        self.data.x = 2 * x
        return 0


@sp.add_test()
def test():
    s = sp.test_scenario("Effects")
    lib = main.Library()
    lib2 = main.Library2()
    main_ = main.Main()
    remote = main.Remote()
    s += lib
    s += lib2
    s += main_
    s += remote

    if s.simulation_mode() is sp.SimulationMode.MOCKUP:
        s.p("mockups - TODO lambda value with effects")
        return

    # Using a storage-modifying lambda from another contract with the
    # same storage:
    main_.run(f=lib.get_set_f(), x=5)
    s.verify(main_.data.x == 5)
    s.verify(lib.data.x == 0)

    # Same, but with Library2:
    main_.run(f=lib2.get_set_f(), x=5)
    s.verify(main_.data.x == 5)
    s.verify(lib.data.x == 0)

    # Same, but overwrite the storage immediately:
    main_.save(f=lib.get_set_f(), x=5)
    s.verify(main_.data.x == 500)
    s.verify(lib.data.x == 0)

    # Complicate things a little by doing it via a remote contract
    # that doesn't have any state:
    remote.call(lib=lib.address, main=main_.address, x=7)
    s.verify(main_.data.x == 7)
    s.verify(lib.data.x == 0)

    # We can also define effectful lambdas outside contracts, but then
    # we have to specify a storage_type:
    main_.run(f=main.f, x=42)
    s.verify(main_.data.x == 84)
