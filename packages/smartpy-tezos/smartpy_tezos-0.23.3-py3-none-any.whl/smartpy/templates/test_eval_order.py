import smartpy as sp


@sp.module
def main():
    class Sub(sp.Contract):
        @sp.onchain_view()
        def my_view(self):
            return 42

    class Main(sp.Contract):
        def __init__(self, sub):
            self.data.x = ""
            self.data.sub = sub

        @sp.private(with_storage="read-write")
        def f_unit(self, x):
            self.data.x = x
            return ()

        @sp.private(with_storage="read-write")
        def f_int(self, x) -> sp.int:
            self.data.x = sp.fst(x)
            return sp.snd(x)

        @sp.private(with_storage="read-write")
        def f_nat(self, x) -> sp.nat:
            self.data.x = sp.fst(x)
            return sp.snd(x)

        @sp.private(with_storage="read-write")
        def f_string(self, x) -> sp.string:
            self.data.x = sp.fst(x)
            return sp.snd(x)

        @sp.private(with_storage="read-write")
        def f_bytes(self, x) -> sp.bytes:
            self.data.x = sp.fst(x)
            return sp.snd(x)

        @sp.private(with_storage="read-write")
        def f_mutez(self, x) -> sp.mutez:
            self.data.x = sp.fst(x)
            return sp.snd(x)

        @sp.private(with_storage="read-write")
        def f_timestamp(self, x) -> sp.timestamp:
            self.data.x = sp.fst(x)
            return sp.snd(x)

        @sp.private(with_storage="read-write")
        def f_bool(self, x) -> sp.bool:
            self.data.x = sp.fst(x)
            return sp.snd(x)

        @sp.private(with_storage="read-write")
        def f_map_int(self, x) -> sp.map[sp.int, sp.int]:
            self.data.x = sp.fst(x)
            return sp.snd(x)

        @sp.private(with_storage="read-write")
        def f_map_nat(self, x) -> sp.map[sp.nat, sp.nat]:
            self.data.x = sp.fst(x)
            return sp.snd(x)

        @sp.private(with_storage="read-write")
        def f_set_nat(self, x) -> sp.set[sp.nat]:
            self.data.x = sp.fst(x)
            return sp.snd(x)

        @sp.private(with_storage="read-write")
        def f_list_int(self, x) -> sp.list[sp.int]:
            self.data.x = sp.fst(x)
            return sp.snd(x)

        @sp.private(with_storage="read-write")
        def f_list_nat(self, x) -> sp.list[sp.nat]:
            self.data.x = sp.fst(x)
            return sp.snd(x)

        # @sp.private(with_storage="read-write")
        # def f_pair(self,x):
        #     self.data.x = sp.fst(x)
        #     return sp.cast(sp.snd(x), sp.pair[sp.nat,sp.nat])

        @sp.private(with_storage="read-write")
        def f_option(self, x) -> sp.option[sp.int]:
            self.data.x = sp.fst(x)
            return sp.snd(x)

        @sp.private(with_storage="read-write")
        def f_option_key_hash(self, x) -> sp.option[sp.key_hash]:
            self.data.x = sp.fst(x)
            return sp.snd(x)

        @sp.private(with_storage="read-write")
        def f_lambda(self, x) -> sp.lambda_(sp.int, sp.int):
            self.data.x = sp.fst(x)
            return sp.snd(x)

        # @sp.private(with_storage="read-write")
        # def f_chest(self,x):
        #     self.data.x = sp.fst(x)
        #     sp.result(sp.cast(sp.snd(x), sp.TChest))

        @sp.private(with_storage="read-write")
        def f_contract(self, x) -> sp.contract[sp.int]:
            self.data.x = sp.fst(x)
            return sp.snd(x)

        # @sp.private(with_storage="read-write")
        # def f_chest_key(self,x):
        #     self.data.x = sp.fst(x)
        #     sp.result(sp.cast(sp.snd(x), sp.TChest_key))

        @sp.private(with_storage="read-write")
        def f_lambda2(self, x) -> sp.lambda_(sp.pair[sp.int, sp.int], sp.int):
            self.data.x = sp.fst(x)
            return sp.snd(x)

        # @sp.private(with_storage="read-write")
        # def f_address(self,x):
        #     self.data.x = sp.fst(x)
        #     return sp.cast(sp.snd(x), sp.address)

        # @sp.private(with_storage="read-write")
        # def f_ticket(self,x):
        #     (x1, x2) = x
        #     self.data.x = x1
        #     return sp.cast(x2, sp.ticket[sp.int])

        @sp.private(with_storage="read-write")
        def f_key(self, x) -> sp.key:
            (x1, x2) = x
            self.data.x = x1
            return x2

        @sp.private(with_storage="read-write")
        def f_signature(self, x) -> sp.signature:
            (x1, x2) = x
            self.data.x = x1
            return x2

        @sp.entrypoint
        def test_prim2(self):
            _ = self.f_map_int(("A", {})).get_opt(self.f_int(("B", 1)))
            assert self.data.x == "A"
            _ = self.f_map_int(("A", {})).contains(self.f_int(("B", 1)))
            assert self.data.x == "A"
            _ = self.f_lambda(("A", lambda x: x))(self.f_int(("B", 1)))
            assert self.data.x == "B"
            _ = self.f_lambda2(("A", lambda _: 0)).apply(self.f_int(("B", 1)))
            assert self.data.x == "A"
            _ = sp.cons(self.f_int(("A", 1)), self.f_list_int(("B", [])))
            assert self.data.x == "A"
            _ = sp.add_seconds(
                self.f_timestamp(("A", sp.timestamp(1))), self.f_int(("B", 1))
            )
            assert self.data.x == "A"
            _ = sp.ticket(self.f_int(("A", 1)), self.f_nat(("B", 1)))
            assert self.data.x == "A"
            # _ = sp.view("my_view", a_address, b_unit)
            # assert self.data.x == "A"

            _ = self.f_int(("A", 1)) + self.f_int(("B", 1))
            assert self.data.x == "A"
            _ = self.f_int(("A", 1)) * self.f_int(("B", 1))
            assert self.data.x == "A"
            _ = self.f_int(("A", 1)) - self.f_int(("B", 1))
            assert self.data.x == "A"
            _ = self.f_int(("A", 1)) + self.f_int(("B", 1))
            assert self.data.x == "A"
            _ = self.f_nat(("A", 1)) / self.f_nat(("B", 1))
            assert self.data.x == "A"
            _ = self.f_int(("A", 1)) == self.f_int(("B", 1))
            assert self.data.x == "A"
            _ = self.f_int(("A", 1)) != self.f_int(("B", 1))
            assert self.data.x == "A"
            _ = self.f_int(("A", 1)) < self.f_int(("B", 1))
            assert self.data.x == "A"
            _ = self.f_int(("A", 1)) <= self.f_int(("B", 1))
            assert self.data.x == "A"
            _ = self.f_int(("A", 1)) > self.f_int(("B", 1))
            assert self.data.x == "A"
            _ = self.f_int(("A", 1)) >= self.f_int(("B", 1))
            assert self.data.x == "A"
            _ = sp.mod(self.f_int(("A", 1)), self.f_int(("B", 1)))
            assert self.data.x == "A"
            _ = self.f_nat(("A", 1)) ^ self.f_nat(("B", 1))
            assert self.data.x == "A"
            _ = sp.min(self.f_int(("A", 1)), self.f_int(("B", 1)))
            assert self.data.x == "A"
            _ = sp.max(self.f_int(("A", 1)), self.f_int(("B", 1)))
            assert self.data.x == "A"
            _ = sp.ediv(self.f_int(("A", 1)), self.f_int(("B", 1)))
            assert self.data.x == "A"

            _ = self.f_bool(("A", False)) or self.f_bool(("B", False))
            assert self.data.x == "B"
            _ = self.f_bool(("A", False)) or self.f_bool(("B", True))
            assert self.data.x == "B"
            _ = self.f_bool(("A", True)) or self.f_bool(("B", False))
            assert self.data.x == "A"
            _ = self.f_bool(("A", True)) or self.f_bool(("B", True))
            assert self.data.x == "A"

            _ = self.f_bool(("A", False)) and self.f_bool(("B", False))
            assert self.data.x == "A"
            _ = self.f_bool(("A", False)) and self.f_bool(("B", True))
            assert self.data.x == "A"
            _ = self.f_bool(("A", True)) and self.f_bool(("B", False))
            assert self.data.x == "B"
            _ = self.f_bool(("A", True)) and self.f_bool(("B", True))
            assert self.data.x == "B"

        @sp.entrypoint
        def test_prim3(self):
            _ = sp.split_tokens(
                self.f_mutez(("A", sp.mutez(1))),
                self.f_nat(("B", 1)),
                self.f_nat(("C", 1)),
            )
            assert self.data.x == "A"
            _ = sp.split_tokens(sp.mutez(0), self.f_nat(("B", 1)), self.f_nat(("C", 1)))
            assert self.data.x == "B"

            _ = range(self.f_nat(("A", 1)), self.f_nat(("B", 1)), self.f_nat(("C", 1)))
            assert (
                self.data.x == "A"
            )  # TODO Check if there is still interpreter-compiler inconsistency

            _ = sp.update_map(
                self.f_int(("A", 1)),
                self.f_option(("B", sp.Some(1))),
                self.f_map_int(("C", {})),
            )
            assert self.data.x == "A"
            _ = sp.update_map(
                0, self.f_option(("B", sp.Some(1))), self.f_map_int(("C", {}))
            )
            assert self.data.x == "B"

            _ = sp.get_and_update(
                self.f_int(("A", 1)),
                self.f_option(("B", sp.Some(1))),
                self.f_map_int(("C", {})),
            )
            assert self.data.x == "A"
            _ = sp.get_and_update(
                0,
                self.f_option(("B", sp.Some(1))),
                self.f_map_int(("C", {})),
            )
            assert self.data.x == "B"

            _ = (
                self.f_int(("B", 1))
                if self.f_bool(("A", True))
                else self.f_int(("C", 1))
            )
            assert self.data.x == "B"
            _ = 0 if self.f_bool(("A", True)) else self.f_int(("C", 1))
            assert self.data.x == "A"

            _ = (
                self.f_int(("B", 1))
                if self.f_bool(("A", False))
                else self.f_int(("C", 1))
            )
            assert self.data.x == "C"
            _ = self.f_int(("B", 1)) if self.f_bool(("A", False)) else 0
            assert self.data.x == "A"

        @sp.entrypoint
        def test_mprim2(self):
            _ = self.f_nat(("A", 1)) << self.f_nat(("B", 1))
            assert self.data.x == "A"

            _ = self.f_nat(("A", 1)) >> self.f_nat(("B", 1))
            assert self.data.x == "A"

        @sp.entrypoint
        def test_mprim3(self, p):
            # sp.cast(p.chest_key, sp.chest_key)

            #     # chest     = sp.chest("0xbcf89e8a80d99cd49690dda59accc4d381c1a3facbacc1a3f9aab5e7ecdc8db6b0928eed84a7e5d9958e96b5b1f3c8ddd9b98dd394f9bafaafad85a2d7cbffeec1e280d5c6ccbab3caddb5ced3c1d39c82cea0cc99b7f788bbca85eeb1badd91fdc8e1e1e9a6cddca7bdef8faaf6acf2aeef8ccbd3d987f6d0ecf9c8c9818c92eb8a81e385fff9e8c4ad96d6e7bad6a480ec83f3cb84bedeac82baafa1b88bfd90968b9ee7b2d8aabef9d8e0d9a9c8a5a8859a8db5e6d496de95cfd2cfc4dcfae3edf9f1d5faee998694ed8aada2a7d4b88aecc8acda98d6f69cfb8df3a5ca80b48d91aa9bbbf68f918998ddc5d3cc82d3f0ce81869fd9edb8b0989dcfa5e9b59db18dd099c7b8bb848586afc7c8888f86d2c6988eeee5e5fbfc9de8a7f19e84ebc2b687049390ebd5cecb86eecfe2bef994f9a7c3eabeabdda0b4b7b59381a8a4c3d7c1b382bcf6e1adb2e3c6ce9ca5e0c0a0beb999f4eacc89cf858fb282b294d99ec2daccd9cdcc98a98b8cb5b0bbf9ed80b0f6ccd2a994f3a1faafbbacf7eebbec9399bfdfd1f0da9ee4aa9dcb8b9c85fcab87bd86b98fd7cc9a8cb2e3cc93ef86df83e5ce9bbda8c7d4cad0e4b893fde8e18b9cf283f9829f9ab8f48da8b0f1b5c8f3a1d2a1a6e5c1fec0abb09eb9b0c2c3ae9f9df6c6a7bad396f7b3b1fc90e490a4f2a5f599fedbc8b3b297a99db3b285a3f0acefe0c8d4cec08195af8098d0f4b8d488bdacd7e8effea5cdaf8dd1ccdbe4fee59eb7e1cebff2eb839b8f81d598abc798d5bdcea59bfcbaf89fbdbbcb8182a3eea1f4f5dccafcb4ddd4ff83d3879edef5d3ca06d2f1146cf4c25faf0e432bf540b4de74fae3cc68e0bc57c700000021cf744e778f4d5e220d4be7310077e6735795b6c90bbe2bdcdd9b686e3c71f833f2")

            #     # a_chest_key  = self.f_chest_key(("A", p.chest_key))

            #     # b_chest      = self.f_chest(("B", chest))

            #     # Time-lock is deprecated.
            #     # _ = sp.open_chest(a_chest_key, b_chest, self.f_nat(("C", 1)))
            #     # assert self.data.x == "A"
            #     # _ = sp.open_chest(p.chest_key, b_chest, self.f_nat(("C", 1)))
            #     # assert self.data.x == "B"

            assert sp.check_signature(
                self.f_key(("A", p.key)),
                self.f_signature(("B", p.signature)),
                self.f_bytes(("C", sp.bytes("0x00"))),
            )
            assert self.data.x == "A"
            assert sp.check_signature(
                p.key,
                self.f_signature(("B", p.signature)),
                self.f_bytes(("C", sp.bytes("0x00"))),
            )
            assert self.data.x == "B"

        @sp.entrypoint
        def test_expr_other(self):
            #     _ = self.f_option(("A", sp.Some(1))).unwrap_some(self.f_int(("B", 1)))
            #     assert self.data.x == "A"
            #     _ = sp.Some(1).unwrap_some(self.f_int(("B", 1)))
            #     assert self.data.x == "A"

            _ = self.f_map_int(("A", {1: 2}))[self.f_int(("B", 1))]
            assert self.data.x == "B"
            _ = (self.f_int(("A", 1)), self.f_int(("B", 1)))
            assert self.data.x == "A"
            _ = sp.record(a=self.f_int(("A", 1)), b=self.f_int(("B", 1)))
            # assert self.data.x == "A" # TODO order + Check if there is still interpreter-compiler inconsistency
            _ = [self.f_int(("A", 1)), self.f_int(("B", 1))]
            assert self.data.x == "A"
            _ = {self.f_int(("A", 1)), self.f_int(("B", 1))}
            assert self.data.x == "A"
            _ = {
                self.f_int(("A", 1)): self.f_int(("B", 1)),
                self.f_int(("C", 1)): self.f_int(("D", 1)),
            }
            # assert self.data.x == "A" # TODO order
            _ = {1: self.f_int(("B", 1)), self.f_int(("C", 1)): self.f_int(("D", 1))}
            # assert self.data.x == "B" # TODO order
            #     # TODO ESaplingVerifyUpdate
            #     _ = self.f_list_int(("A", [])).map(self.f_lambda(("B", lambda x: x)))
            #     assert self.data.x == "A"

            m = {}
            # self.f_map_nat(("A", m))[self.f_nat(("B", 1))] = len(self.f_map_nat(("C", m)))
            m[self.f_nat(("B", 1))] = len(self.f_map_nat(("C", m)))
            assert self.data.x == "B" and m[1] == 0 and len(m) == 1
            # self.f_map_nat(("A", m))[self.f_nat(("B", 2))] = len(self.f_map_nat(("C", m)))
            m[self.f_nat(("B", 2))] = len(self.f_map_nat(("C", m)))
            assert self.data.x == "B" and m[2] == 1 and len(m) == 2
            s = set()
            # self.f_set_nat(("A", s)).add(len(self.f_set_nat(("B", s))))
            s.add(len(self.f_set_nat(("B", s))))
            assert self.data.x == "B" and s.contains(0) and len(s) == 1
            # self.f_set_nat(("A", s)).add(len(self.f_set_nat(("B", s))))
            s.add(len(self.f_set_nat(("B", s))))
            assert self.data.x == "B" and s.contains(1) and len(s) == 2
            l = []
            # self.f_list_nat(("A", l)).push(len(self.f_list_nat(("B", l))))
            l.push(len(self.f_list_nat(("B", l))))
            assert self.data.x == "B" and sum(l) == 0 and len(l) == 1
            # self.f_list_nat(("A", l)).push(len(self.f_list_nat(("B", l))))
            l.push(len(self.f_list_nat(("B", l))))
            assert self.data.x == "B" and sum(l) == 1 and len(l) == 2

            _ = sp.create_contract_operation(
                Sub,
                self.f_option_key_hash(("A", None)),
                self.f_mutez(("B", sp.mutez(1))),
                self.f_unit(("C")),
            )
            assert self.data.x == "A"
            _ = sp.create_contract_operation(
                Sub, None, self.f_mutez(("B", sp.mutez(1))), self.f_unit(("C"))
            )
            assert self.data.x == "B"

            _ = sp.slice(
                self.f_nat(("A", 1)), self.f_nat(("B", 1)), self.f_string(("C", "abc"))
            )
            assert self.data.x == "A"
            _ = sp.slice(0, self.f_nat(("B", 1)), self.f_string(("C", "abc")))
            assert self.data.x == "B"

            _ = sp.transfer_operation(
                self.f_int(("A", 1)),
                self.f_mutez(("B", sp.mutez(1))),
                self.f_contract(("C", sp.self_entrypoint("put_int"))),
            )
            assert self.data.x == "A"
            _ = sp.transfer_operation(
                0,
                self.f_mutez(("B", sp.mutez(1))),
                self.f_contract(("C", sp.self_entrypoint("put_int"))),
            )
            assert self.data.x == "B"

        @sp.entrypoint
        def put_int(self, x):
            sp.cast(x, sp.int)


@sp.add_test()
def test():
    s = sp.test_scenario("Test_eval_order")

    sub = main.Sub()
    s += sub

    main_ = main.Main(sub.address)
    s += main_

    if s.simulation_mode() is sp.SimulationMode.MOCKUP:
        s.p("mockups - TODO fix")
        return

    main_.test_prim2()
    main_.test_prim3()
    main_.test_mprim2()

    # chest_key = sp.chest_key("0xf5d3cec5da988edfbee8be85b4919bc7c5a3f7ecebe7a19ac8e0c3f9c3aac5948de9b9dddab88b93c4fee4d094a3a5e48494c0ae80b4ffbcd9a8b7a2c9f3dfc0e2e18082f3d3ceabf9f1a7c8fcd4dec7b7e091a89e83f8a6ab90dea1bdbd95bff9ed8ac89c88ebeecfe5faaeb8f184e5df9298e5aff3bad5bbc1fcefdbb5b2929df9c6ced9aebefbc49decb4d9e085b1a8c39099818d97e0b3dbf287efb99c87c8eeb38f86d9e9c2bdeccec4abb5ce89bce988aba5a0adf59180898697a7e5d1dfa8d5a6aac8f0f5bd87ecb7aeaedec6a4f7f5bfead9e1cbd3a8a88fddcb939198f0ae94cecdc3e9d3d9c2b28ece8ff487a0e983868ef995b3ee90f082adf8aeddbab2efc2b5fcd5aff1a19bb3acff83b08986d0ffa3eec4afabbec280f4d498b1f2e6de01c192a381d3b8c19dd8edb4d6e689cbccb1b5c396c7abda9bc4ed9edf9ecff7c78bab8fadbbd4f4e7d1d289eace839becdfa5e7d1ddc2b0e9e1e88d87a3e3aae8c6dd889cd980e69af8b992d4b5e28cb691de94c0afe0f3fbde8b85e4eced9ec8dcd986d189e4a8bcd3fda2efbce5cde9d68499eef7bda5a782c3adf0cc84abd0c0ec91988b9a81ad819af19e97eefacea9a9b1ffe2d1bcc1e5d8dc87e89d8a92afd3fcf4d4d2e1d9e4f583c5a583ebb6f19dd7abd3f8f5d6a8ee9bf78faa8aedf0d8b0e6a1a6bf95849192b5f8bfef9581deaebef3e6f390ac99ade490e7feb5d0d589cce2e3d4b9ced493e3fac1da83f697e6c0e68f8295ec97f2c0aae7dcaffaedb5fef283d4a5b4f3fdd8e7a0b0f9c4accce9c2f9e9ba8b8391fad3d0db84cbe9f3d003")
    alice = sp.test_account("Alice")
    signature = sp.make_signature(
        secret_key=alice.secret_key, message=sp.bytes("0x00"), message_format="Raw"
    )
    # main_.test_mprim3(sp.record(chest_key=chest_key, key=alice.public_key, signature=signature))
    main_.test_mprim3(sp.record(key=alice.public_key, signature=signature))

    main_.test_expr_other()
