import smartpy as sp


@sp.module
def main():
    tv: type = sp.variant(a=sp.int, b=sp.int)

    t1: type = sp.lambda_[sp.int, tv]
    t2: type = sp.lambda_[sp.int, sp.variant(a=sp.int)]
    int_to_string: type = sp.lambda_[sp.int, sp.string]

    def list_equal(lists):
        (l1, l2) = lists
        return sp.len(l1) == sp.len(l2) and sum(l1) == sum(l2)

    class Pack(sp.Contract):
        def __init__(self):
            self.data.unit = sp.bytes("0x05030b")
            self.data.true = sp.bytes("0x05030a")
            self.data.false = sp.bytes("0x050303")
            self.data.mutez_0 = sp.bytes("0x050000")
            self.data.mutez_1 = sp.bytes("0x050001")
            self.data.mutez_2 = sp.bytes("0x050002")
            self.data.mutez_3 = sp.bytes("0x050003")
            self.data.mutez_10 = sp.bytes("0x05000a")
            self.data.mutez_10_000 = sp.bytes("0x0500909c01")
            self.data.mutez_1_000_000 = sp.bytes("0x050080897a")
            self.data.mutez_1_000_000_000_000 = sp.bytes("0x050080c0a8ca9a3a")
            self.data.nat_0 = sp.bytes("0x050000")
            self.data.nat_1 = sp.bytes("0x050001")
            self.data.nat_2 = sp.bytes("0x050002")
            self.data.nat_3 = sp.bytes("0x050003")
            self.data.nat_10 = sp.bytes("0x05000a")
            self.data.nat_10_000 = sp.bytes("0x0500909c01")
            self.data.nat_1_000_000 = sp.bytes("0x050080897a")
            self.data.nat_1_000_000_000_000 = sp.bytes("0x050080c0a8ca9a3a")
            self.data.int_0 = sp.bytes("0x050000")
            self.data.int_1 = sp.bytes("0x050001")
            self.data.int_2 = sp.bytes("0x050002")
            self.data.int_3 = sp.bytes("0x050003")
            self.data.int_10 = sp.bytes("0x05000a")
            self.data.int_10_000 = sp.bytes("0x0500909c01")
            self.data.int_1_000_000 = sp.bytes("0x050080897a")
            self.data.int_1_000_000_000_000 = sp.bytes("0x050080c0a8ca9a3a")
            self.data.int_minus_0 = sp.bytes("0x050000")
            self.data.int_minus_1 = sp.bytes("0x050041")
            self.data.int_minus_2 = sp.bytes("0x050042")
            self.data.int_minus_3 = sp.bytes("0x050043")
            self.data.int_minus_10 = sp.bytes("0x05004a")
            self.data.int_minus_10_000 = sp.bytes("0x0500d09c01")
            self.data.int_minus_1_000_000 = sp.bytes("0x0500c0897a")
            self.data.int_minus_1_000_000_000_000 = sp.bytes("0x0500c0c0a8ca9a3a")
            self.data.string_ = sp.bytes("0x050100000000")
            self.data.string_a = sp.bytes("0x05010000000161")
            self.data.string_ab = sp.bytes("0x0501000000026162")
            self.data.string_abc = sp.bytes("0x050100000003616263")
            self.data.bytes_0x = sp.bytes("0x050a00000000")
            self.data.bytes_0x00 = sp.bytes("0x050a0000000100")
            self.data.bytes_0xab00 = sp.bytes("0x050a00000002ab00")
            self.data.pair_int_1_int_2 = sp.bytes("0x05070700010002")
            self.data.pair_string_a_true = sp.bytes("0x050707010000000161030a")
            self.data.timestamp_123 = sp.bytes("0x0500bb01")
            self.data.signature_sig = sp.bytes(
                "0x050a0000004027bcc456b12981bacfbf9755c589c16772da5200656386f34c46ee2a70a9c07be36268ce666894a5e8a0828027b6fa1a7a084a5ffa24208cc1dfec07d6f66e0f"
            )
            self.data.signature_spsig = sp.bytes(
                "0x050a00000040865b0ceaa2decd64fea1b7e0e97d6ae8035125d821ebe99d7d5c8a559f36fdd43388a570e475011f6d2bbef184ece9bafbf0ac12157f7257988e9575ae2cbca9"
            )
            self.data.signature_p2sig = sp.bytes(
                "0x050a00000040e7b25662eb9bb1e92ef7cb20c2fcaca120eccbe2d6af7511c2e510eb586ca8612d9dfe26bc7882a33b29b8c9706a04124f98dd281f1622d8da50db7a5cd4ab43"
            )
            self.data.signature = sp.bytes(
                "0x050a000000404d6738931b59605ca0449b7b76a01d210ace9220051821ecf43382a7024ed99063c5bedb85c81b919d33a213c6d8fb47f2c9b4deaf6f68f56dee038ea739740f"
            )
            self.data.address_tz1fextP23D6Ph2zeGTP8EwkP5Y8TufeFCHA = sp.bytes(
                "0x050a000000160000db8fc132cf9624febe1675fbfd0c0fcdd7655f23"
            )
            self.data.address_tz2FCNBrERXtaTtNX6iimR1UJ5JSDxvdHM93 = sp.bytes(
                "0x050a0000001600014b7c404fd4fbcf931cde0a8971caf76f53c8e5c0"
            )
            self.data.address_tz3WMqdzXqRWXwyvj5Hp2H7QEepaUuS7vd9K = sp.bytes(
                "0x050a0000001600026e08178148d348cb59efffbdb403ca546b13304e"
            )
            self.data.address_tz4VVJutTUzLVFY64H1HTtNzFB4Uzfisk6Cc = sp.bytes(
                "0x050a000000160003e0b0f0c1fa4d9d46c8281d3e98900f942283b15c"
            )
            self.data.key_hash_tz1fextP23D6Ph2zeGTP8EwkP5Y8TufeFCHA = sp.bytes(
                "0x050a0000001500db8fc132cf9624febe1675fbfd0c0fcdd7655f23"
            )
            self.data.key_hash_tz2FCNBrERXtaTtNX6iimR1UJ5JSDxvdHM93 = sp.bytes(
                "0x050a00000015014b7c404fd4fbcf931cde0a8971caf76f53c8e5c0"
            )
            self.data.key_hash_tz3WMqdzXqRWXwyvj5Hp2H7QEepaUuS7vd9K = sp.bytes(
                "0x050a00000015026e08178148d348cb59efffbdb403ca546b13304e"
            )
            self.data.key_hash_tz4VVJutTUzLVFY64H1HTtNzFB4Uzfisk6Cc = sp.bytes(
                "0x050a0000001503e0b0f0c1fa4d9d46c8281d3e98900f942283b15c"
            )
            self.data.address_KT1Mpqi89gRyUuoXUPAWjHkqkk1F48eUKUVy = sp.bytes(
                "0x050a00000016019142eb01374f37f03023eefc82f2ede96e8ae51500"
            )
            self.data.address_KT1Mpqi89gRyUuoXUPAWjHkqkk1F48eUKUVy_ = sp.bytes(
                "0x050a00000016019142eb01374f37f03023eefc82f2ede96e8ae51500"
            )
            self.data.address_KT1Mpqi89gRyUuoXUPAWjHkqkk1F48eUKUVy_foo = sp.bytes(
                "0x050a00000019019142eb01374f37f03023eefc82f2ede96e8ae51500666f6f"
            )
            self.data.list_int_0_to_6 = sp.bytes(
                "0x05020000000e0000000100020003000400050006"
            )
            self.data.list_int_range_0_1 = sp.bytes("0x0502000000020000")
            self.data.list_int_range_0_2 = sp.bytes("0x05020000000400000001")
            self.data.list_int_range_0_3 = sp.bytes("0x050200000006000000010002")
            self.data.list_int_range_0_4 = sp.bytes("0x0502000000080000000100020003")
            self.data.list_int_range_0_5 = sp.bytes(
                "0x05020000000a00000001000200030004"
            )
            self.data.list_int_range_0_6 = sp.bytes(
                "0x05020000000c000000010002000300040005"
            )
            self.data.list_int_range_0_7 = sp.bytes(
                "0x05020000000e0000000100020003000400050006"
            )
            self.data.set_int_1_to_4 = sp.bytes("0x0502000000080001000200030004")

            self.data.lambda_x_plus_2 = sp.bytes("0x0502000000080743035b00020312")
            self.data.lambda_f1 = sp.bytes(
                "0x05020000001b03210316072c020000000903200743035b00bb0102000000020317"
            )
            self.data.lambda_f2 = sp.bytes(
                "0x05020000002703210316072c020000000903200743035b00bb01020000000e032105290004034c052900030312"
            )
            self.data.lambda_f3 = sp.bytes(
                "0x05020000004c0743035b000007430368010000000141052100030325072c0200000022034c0570000203190325072c020000000c03200743036801000000014202000000000200000008034c0320034c0320"
            )
            self.data.lambda_michelson = sp.bytes(
                "0x05020000000c03210743035b002a0312033a"
            )

            self.data.list_string = sp.bytes(
                "05020000002201000000057468697320010000000369732001000000026120010000000474657374"
            )
            self.data.map_string_int = sp.bytes(
                "05020000000f07040100000006616e73776572002a"
            )
            self.data.record_string_int = sp.bytes("05070701000000047465737400b914")
            self.data.variant_a_string_b_nat = sp.bytes("050505010000000474657374")
            self.data.option_string = sp.bytes("050509010000000568656c6c6f")
            self.data.none_string = sp.bytes("050306")

            # Activate when sapling is implemented
            # self.data.sapling_transaction = sp.bytes("0x00")
            # self.data.sapling_state = sp.bytes("0x00")

            self.data.chain_id = sp.bytes("050a00000004af1864d9")  # NetXnHfVqm9iesp
            self.data.level_2548242 = sp.bytes("05009288b702")  # 2548242

        @sp.private()
        def f1(self, x):
            if x.a:
                return 123
            else:
                return x.b

        @sp.private()
        def f2(self, x):
            sp.cast(x.b, sp.int)
            if x.a:
                return 123
            else:
                return x.b + x.c

        @sp.private()
        def f3(self, x):
            y = 0
            r = "A"
            if x == 0:
                if x == y:
                    r = "B"
            return r

        @sp.entrypoint
        def pack(self, signature_sig, signature_spsig, signature_p2sig, s):
            sp.cast(signature_sig, sp.signature)
            sp.cast(signature_spsig, sp.signature)
            sp.cast(signature_p2sig, sp.signature)
            sp.cast(s, sp.signature)
            assert self.data.unit == sp.pack(())
            assert self.data.true == sp.pack(True)
            assert self.data.false == sp.pack(False)
            assert self.data.mutez_0 == sp.pack(sp.mutez(0))
            assert self.data.mutez_1 == sp.pack(sp.mutez(1))
            assert self.data.mutez_2 == sp.pack(sp.mutez(2))
            assert self.data.mutez_3 == sp.pack(sp.mutez(3))
            assert self.data.mutez_10 == sp.pack(sp.mutez(10))
            assert self.data.mutez_10_000 == sp.pack(sp.mutez(10000))
            assert self.data.mutez_1_000_000 == sp.pack(sp.mutez(1000000))
            assert self.data.mutez_1_000_000_000_000 == sp.pack(sp.mutez(1000000000000))
            assert self.data.nat_0 == sp.pack(sp.nat(0))
            assert self.data.nat_1 == sp.pack(sp.nat(1))
            assert self.data.nat_2 == sp.pack(sp.nat(2))
            assert self.data.nat_3 == sp.pack(sp.nat(3))
            assert self.data.nat_10 == sp.pack(sp.nat(10))
            assert self.data.nat_10_000 == sp.pack(sp.nat(10000))
            assert self.data.nat_1_000_000 == sp.pack(sp.nat(1000000))
            assert self.data.nat_1_000_000_000_000 == sp.pack(sp.nat(1000000000000))
            assert self.data.int_0 == sp.pack(sp.int(0))
            assert self.data.int_1 == sp.pack(sp.int(1))
            assert self.data.int_2 == sp.pack(sp.int(2))
            assert self.data.int_3 == sp.pack(sp.int(3))
            assert self.data.int_10 == sp.pack(sp.int(10))
            assert self.data.int_10_000 == sp.pack(sp.int(10000))
            assert self.data.int_1_000_000 == sp.pack(sp.int(1000000))
            assert self.data.int_1_000_000_000_000 == sp.pack(sp.int(1000000000000))
            assert self.data.int_minus_0 == sp.pack(sp.int(-0))
            assert self.data.int_minus_1 == sp.pack(sp.int(-1))
            assert self.data.int_minus_2 == sp.pack(sp.int(-2))
            assert self.data.int_minus_3 == sp.pack(sp.int(-3))
            assert self.data.int_minus_10 == sp.pack(sp.int(-10))
            assert self.data.int_minus_10_000 == sp.pack(sp.int(-10000))
            assert self.data.int_minus_1_000_000 == sp.pack(sp.int(-1000000))
            assert self.data.int_minus_1_000_000_000_000 == sp.pack(
                sp.int(-1000000000000)
            )
            assert self.data.string_ == sp.pack("")
            assert self.data.string_a == sp.pack("a")
            assert self.data.string_ab == sp.pack("ab")
            assert self.data.string_abc == sp.pack("abc")
            assert self.data.bytes_0x == sp.pack(sp.bytes("0x"))
            assert self.data.bytes_0x00 == sp.pack(sp.bytes("0x00"))
            assert self.data.bytes_0xab00 == sp.pack(sp.bytes("0xab00"))
            assert self.data.pair_int_1_int_2 == sp.pack((1, 2))
            assert self.data.pair_string_a_true == sp.pack(("a", True))
            assert self.data.timestamp_123 == sp.pack(sp.timestamp(123))
            # assert self.data.signature_sig == sp.pack(sp.signature("sigTBpkXw6tC72L2nJ2r2Jm5iB6uidTWqoMNd4oEawUbGBf5mHVfKawFYL8X8MJECpL73oBnfujyUZNLK2LQWD1FaCkYMP4j"))
            # assert self.data.signature_spsig == sp.pack(sp.signature("spsig1PPUFZucuAQybs5wsqsNQ68QNgFaBnVKMFaoZZfi1BtNnuCAWnmL9wVy5HfHkR6AeodjVGxpBVVSYcJKyMURn6K1yknYLm"))
            # assert self.data.signature_p2sig == sp.pack(sp.signature("p2sigsceCzcDw2AeYDzUonj4JT341WC9Px4wdhHBxbZcG1FhfqFVuG7f2fGCzrEHSAZgrsrQWpxduDPk9qZRgrpzwJnSHC3gZJ"))
            # assert self.data.signature == sp.pack(s)

            assert self.data.signature_sig == sp.pack(signature_sig)
            # assert self.data.signature_spsig == sp.pack(signature_spsig)
            # assert self.data.signature_p2sig == sp.pack(signature_p2sig)
            # self.data.signature = sp.pack(s)
            assert self.data.address_tz1fextP23D6Ph2zeGTP8EwkP5Y8TufeFCHA == sp.pack(
                sp.address("tz1fextP23D6Ph2zeGTP8EwkP5Y8TufeFCHA")
            )
            assert self.data.address_tz2FCNBrERXtaTtNX6iimR1UJ5JSDxvdHM93 == sp.pack(
                sp.address("tz2FCNBrERXtaTtNX6iimR1UJ5JSDxvdHM93")
            )
            assert self.data.address_tz3WMqdzXqRWXwyvj5Hp2H7QEepaUuS7vd9K == sp.pack(
                sp.address("tz3WMqdzXqRWXwyvj5Hp2H7QEepaUuS7vd9K")
            )
            assert self.data.key_hash_tz1fextP23D6Ph2zeGTP8EwkP5Y8TufeFCHA == sp.pack(
                sp.key_hash("tz1fextP23D6Ph2zeGTP8EwkP5Y8TufeFCHA")
            )
            assert self.data.key_hash_tz2FCNBrERXtaTtNX6iimR1UJ5JSDxvdHM93 == sp.pack(
                sp.key_hash("tz2FCNBrERXtaTtNX6iimR1UJ5JSDxvdHM93")
            )
            assert self.data.key_hash_tz3WMqdzXqRWXwyvj5Hp2H7QEepaUuS7vd9K == sp.pack(
                sp.key_hash("tz3WMqdzXqRWXwyvj5Hp2H7QEepaUuS7vd9K")
            )
            # TODO activate when tz4 are implemented
            # assert self.data.key_hash_tz4VVJutTUzLVFY64H1HTtNzFB4Uzfisk6Cc == sp.pack(sp.key_hash("tz4VVJutTUzLVFY64H1HTtNzFB4Uzfisk6Cc"))
            assert self.data.address_KT1Mpqi89gRyUuoXUPAWjHkqkk1F48eUKUVy == sp.pack(
                sp.address("KT1Mpqi89gRyUuoXUPAWjHkqkk1F48eUKUVy")
            )
            assert self.data.address_KT1Mpqi89gRyUuoXUPAWjHkqkk1F48eUKUVy_ == sp.pack(
                sp.address("KT1Mpqi89gRyUuoXUPAWjHkqkk1F48eUKUVy%")
            )
            assert (
                self.data.address_KT1Mpqi89gRyUuoXUPAWjHkqkk1F48eUKUVy_foo
                == sp.pack(sp.address("KT1Mpqi89gRyUuoXUPAWjHkqkk1F48eUKUVy%foo"))
            )
            assert self.data.list_int_0_to_6 == sp.pack([0, 1, 2, 3, 4, 5, 6])
            assert self.data.list_int_range_0_1 == sp.pack(range(0, 1))
            assert self.data.list_int_range_0_2 == sp.pack(range(0, 2))
            assert self.data.list_int_range_0_3 == sp.pack(range(0, 3))
            assert self.data.list_int_range_0_4 == sp.pack(range(0, 4))
            assert self.data.list_int_range_0_5 == sp.pack(range(0, 5))
            assert self.data.list_int_range_0_6 == sp.pack(range(0, 6))
            assert self.data.list_int_range_0_7 == sp.pack(range(0, 7))
            assert self.data.set_int_1_to_4 == sp.pack({1, 2, 3, 4})

            assert self.data.lambda_x_plus_2 == sp.pack(lambda x: x + 2)
            assert self.data.lambda_f1 == sp.pack(self.f1)
            assert self.data.lambda_f2 == sp.pack(self.f2)
            assert self.data.lambda_f3 == sp.pack(self.f3)
            assert self.data.lambda_michelson == sp.pack(
                lambda x: sp.michelson(
                    "DUP; PUSH int 42; ADD; MUL", [sp.int], [sp.int], x
                )
            )

            assert self.data.list_string == sp.pack(["this ", "is ", "a ", "test"])
            assert self.data.map_string_int == sp.pack({"answer": 42})
            assert self.data.record_string_int == sp.pack(sp.record(a="test", b=1337))
            assert self.data.variant_a_string_b_nat == sp.pack(
                sp.cast(sp.variant.a("test"), sp.variant(a=sp.string, b=sp.nat))
            )
            assert self.data.option_string == sp.pack(
                sp.cast(sp.Some("hello"), sp.option[sp.string])
            )
            assert self.data.none_string == sp.pack(sp.cast(None, sp.option[sp.string]))

            # assert self.data.chain_id == sp.pack(sp.chain_id)
            # TODO when chain_id creation is implemented
            # assert self.data.chain_id == sp.chain_id("NetXnHfVqm9iesp")
            assert self.data.level_2548242 == sp.pack(sp.level)
            assert self.data.level_2548242 == sp.pack(sp.nat(2548242))

            # TODO: activate when sapling is implemented
            # assert self.data.sapling_transaction = sp.pack(...)
            # assert self.data.sapling_state = sp.pack(...)

        @sp.entrypoint
        def unpack(self, signature_sig, signature_spsig, signature_p2sig, s):
            sp.cast(signature_sig, sp.signature)
            sp.cast(signature_spsig, sp.signature)
            sp.cast(signature_p2sig, sp.signature)
            sp.cast(s, sp.signature)
            assert sp.unpack(self.data.unit, sp.unit).unwrap_some() == ()
            assert sp.unpack(self.data.true, sp.bool).unwrap_some() == True
            assert sp.unpack(self.data.false, sp.bool).unwrap_some() == False
            assert sp.unpack(self.data.mutez_0, sp.mutez).unwrap_some() == sp.mutez(0)
            assert sp.unpack(self.data.mutez_1, sp.mutez).unwrap_some() == sp.mutez(1)
            assert sp.unpack(self.data.mutez_2, sp.mutez).unwrap_some() == sp.mutez(2)
            assert sp.unpack(self.data.mutez_3, sp.mutez).unwrap_some() == sp.mutez(3)
            assert sp.unpack(self.data.mutez_10, sp.mutez).unwrap_some() == sp.mutez(10)
            assert sp.unpack(
                self.data.mutez_10_000, sp.mutez
            ).unwrap_some() == sp.mutez(10000)
            assert sp.unpack(
                self.data.mutez_1_000_000, sp.mutez
            ).unwrap_some() == sp.mutez(1000000)
            assert sp.unpack(
                self.data.mutez_1_000_000_000_000, sp.mutez
            ).unwrap_some() == sp.mutez(1000000000000)
            assert sp.unpack(self.data.nat_0, sp.nat).unwrap_some() == sp.nat(0)
            assert sp.unpack(self.data.nat_1, sp.nat).unwrap_some() == sp.nat(1)
            assert sp.unpack(self.data.nat_2, sp.nat).unwrap_some() == sp.nat(2)
            assert sp.unpack(self.data.nat_3, sp.nat).unwrap_some() == sp.nat(3)
            assert sp.unpack(self.data.nat_10, sp.nat).unwrap_some() == sp.nat(10)
            assert sp.unpack(self.data.nat_10_000, sp.nat).unwrap_some() == sp.nat(
                10000
            )
            assert sp.unpack(self.data.nat_1_000_000, sp.nat).unwrap_some() == sp.nat(
                1000000
            )
            assert sp.unpack(
                self.data.nat_1_000_000_000_000, sp.nat
            ).unwrap_some() == sp.nat(1000000000000)
            assert sp.unpack(self.data.int_0, sp.int).unwrap_some() == sp.int(0)
            assert sp.unpack(self.data.int_1, sp.int).unwrap_some() == sp.int(1)
            assert sp.unpack(self.data.int_2, sp.int).unwrap_some() == sp.int(2)
            assert sp.unpack(self.data.int_3, sp.int).unwrap_some() == sp.int(3)
            assert sp.unpack(self.data.int_10, sp.int).unwrap_some() == sp.int(10)
            assert sp.unpack(self.data.int_10_000, sp.int).unwrap_some() == sp.int(
                10000
            )
            assert sp.unpack(self.data.int_1_000_000, sp.int).unwrap_some() == sp.int(
                1000000
            )
            assert sp.unpack(
                self.data.int_1_000_000_000_000, sp.int
            ).unwrap_some() == sp.int(1000000000000)
            assert sp.unpack(self.data.int_minus_0, sp.int).unwrap_some() == sp.int(-0)
            assert sp.unpack(self.data.int_minus_1, sp.int).unwrap_some() == sp.int(-1)
            assert sp.unpack(self.data.int_minus_2, sp.int).unwrap_some() == sp.int(-2)
            assert sp.unpack(self.data.int_minus_3, sp.int).unwrap_some() == sp.int(-3)
            assert sp.unpack(self.data.int_minus_10, sp.int).unwrap_some() == sp.int(
                -10
            )
            assert sp.unpack(
                self.data.int_minus_10_000, sp.int
            ).unwrap_some() == sp.int(-10000)
            assert sp.unpack(
                self.data.int_minus_1_000_000, sp.int
            ).unwrap_some() == sp.int(-1000000)
            assert sp.unpack(
                self.data.int_minus_1_000_000_000_000, sp.int
            ).unwrap_some() == sp.int(-1000000000000)
            assert sp.unpack(self.data.string_, sp.string).unwrap_some() == ""
            assert sp.unpack(self.data.string_a, sp.string).unwrap_some() == "a"
            assert sp.unpack(self.data.string_ab, sp.string).unwrap_some() == "ab"
            assert sp.unpack(self.data.string_abc, sp.string).unwrap_some() == "abc"
            assert sp.unpack(self.data.bytes_0x, sp.bytes).unwrap_some() == sp.bytes(
                "0x"
            )
            assert sp.unpack(self.data.bytes_0x00, sp.bytes).unwrap_some() == sp.bytes(
                "0x00"
            )
            assert sp.unpack(
                self.data.bytes_0xab00, sp.bytes
            ).unwrap_some() == sp.bytes("0xab00")
            assert sp.unpack(
                self.data.pair_int_1_int_2, sp.pair[sp.int, sp.int]
            ).unwrap_some() == (1, 2)
            assert sp.unpack(
                self.data.pair_string_a_true, sp.pair[sp.string, sp.bool]
            ).unwrap_some() == ("a", True)
            assert sp.unpack(
                self.data.timestamp_123, sp.timestamp
            ).unwrap_some() == sp.timestamp(123)
            assert (
                sp.unpack(self.data.signature_sig, sp.signature).unwrap_some()
                == signature_sig
            )
            # assert sp.unpack(self.data.signature_spsig, sp.signature).unwrap_some() == signature_spsig
            # assert sp.unpack(self.data.signature_p2sig, sp.signature).unwrap_some() == signature_p2sig
            # assert sp.unpack(self.data.signature, sp.signature).unwrap_some() == s
            assert sp.unpack(
                self.data.address_tz1fextP23D6Ph2zeGTP8EwkP5Y8TufeFCHA, sp.address
            ).unwrap_some() == sp.address("tz1fextP23D6Ph2zeGTP8EwkP5Y8TufeFCHA")
            assert sp.unpack(
                self.data.address_tz2FCNBrERXtaTtNX6iimR1UJ5JSDxvdHM93, sp.address
            ).unwrap_some() == sp.address("tz2FCNBrERXtaTtNX6iimR1UJ5JSDxvdHM93")
            assert sp.unpack(
                self.data.address_tz3WMqdzXqRWXwyvj5Hp2H7QEepaUuS7vd9K, sp.address
            ).unwrap_some() == sp.address("tz3WMqdzXqRWXwyvj5Hp2H7QEepaUuS7vd9K")
            # TODO activate when tz4 are implemented
            # assert sp.unpack(self.data.address_tz4VVJutTUzLVFY64H1HTtNzFB4Uzfisk6Cc, sp.address).unwrap_some() == sp.address("tz4VVJutTUzLVFY64H1HTtNzFB4Uzfisk6Cc")
            assert sp.unpack(
                self.data.key_hash_tz1fextP23D6Ph2zeGTP8EwkP5Y8TufeFCHA, sp.key_hash
            ).unwrap_some() == sp.key_hash("tz1fextP23D6Ph2zeGTP8EwkP5Y8TufeFCHA")
            assert sp.unpack(
                self.data.key_hash_tz2FCNBrERXtaTtNX6iimR1UJ5JSDxvdHM93, sp.key_hash
            ).unwrap_some() == sp.key_hash("tz2FCNBrERXtaTtNX6iimR1UJ5JSDxvdHM93")
            assert sp.unpack(
                self.data.key_hash_tz3WMqdzXqRWXwyvj5Hp2H7QEepaUuS7vd9K, sp.key_hash
            ).unwrap_some() == sp.key_hash("tz3WMqdzXqRWXwyvj5Hp2H7QEepaUuS7vd9K")
            # TODO activate when tz4 are implemented
            # assert sp.unpack(self.data.key_hash_tz4VVJutTUzLVFY64H1HTtNzFB4Uzfisk6Cc, sp.key_hash).unwrap_some() == sp.key_hash("tz4VVJutTUzLVFY64H1HTtNzFB4Uzfisk6Ccc")
            assert sp.unpack(
                self.data.address_KT1Mpqi89gRyUuoXUPAWjHkqkk1F48eUKUVy, sp.address
            ).unwrap_some() == sp.address("KT1Mpqi89gRyUuoXUPAWjHkqkk1F48eUKUVy")
            assert sp.unpack(
                self.data.address_KT1Mpqi89gRyUuoXUPAWjHkqkk1F48eUKUVy_, sp.address
            ).unwrap_some() == sp.address("KT1Mpqi89gRyUuoXUPAWjHkqkk1F48eUKUVy")
            assert sp.unpack(
                self.data.address_KT1Mpqi89gRyUuoXUPAWjHkqkk1F48eUKUVy_foo, sp.address
            ).unwrap_some() == sp.address("KT1Mpqi89gRyUuoXUPAWjHkqkk1F48eUKUVy%foo")

            assert list_equal(
                (
                    sp.unpack(self.data.list_int_0_to_6, sp.list[sp.int]).unwrap_some(),
                    [0, 1, 2, 3, 4, 5, 6],
                )
            )
            assert list_equal(
                (
                    sp.unpack(
                        self.data.list_int_range_0_1, sp.list[sp.int]
                    ).unwrap_some(),
                    range(0, 1),
                )
            )
            assert list_equal(
                (
                    sp.unpack(
                        self.data.list_int_range_0_2, sp.list[sp.int]
                    ).unwrap_some(),
                    range(0, 2),
                )
            )
            assert list_equal(
                (
                    sp.unpack(
                        self.data.list_int_range_0_3, sp.list[sp.int]
                    ).unwrap_some(),
                    range(0, 3),
                )
            )
            assert list_equal(
                (
                    sp.unpack(
                        self.data.list_int_range_0_4, sp.list[sp.int]
                    ).unwrap_some(),
                    range(0, 4),
                )
            )
            assert list_equal(
                (
                    sp.unpack(
                        self.data.list_int_range_0_5, sp.list[sp.int]
                    ).unwrap_some(),
                    range(0, 5),
                )
            )
            assert list_equal(
                (
                    sp.unpack(
                        self.data.list_int_range_0_6, sp.list[sp.int]
                    ).unwrap_some(),
                    range(0, 6),
                )
            )
            assert list_equal(
                (
                    sp.unpack(
                        self.data.list_int_range_0_7, sp.list[sp.int]
                    ).unwrap_some(),
                    range(0, 7),
                )
            )
            assert list_equal(
                (
                    sp.unpack(self.data.set_int_1_to_4, sp.set[sp.int])
                    .unwrap_some()
                    .elements(),
                    [1, 2, 3, 4],
                )
            )

            assert sp.pack(
                sp.unpack(
                    self.data.lambda_x_plus_2, sp.lambda_[sp.int, sp.int]
                ).unwrap_some()
            ) == sp.pack(lambda x: x + 2)
            assert sp.pack(
                sp.unpack(
                    self.data.lambda_f1,
                    sp.lambda_[sp.record(a=sp.bool, b=sp.int), sp.int],
                ).unwrap_some()
            ) == sp.pack(self.f1)
            assert sp.pack(
                sp.unpack(
                    self.data.lambda_f2,
                    sp.lambda_[sp.record(a=sp.bool, b=sp.int, c=sp.int), sp.int],
                ).unwrap_some()
            ) == sp.pack(self.f2)
            unpacked_f3 = sp.unpack(
                self.data.lambda_f3, sp.lambda_[sp.int, sp.string]
            ).unwrap_some()
            assert unpacked_f3(0) == self.f3(0)
            assert unpacked_f3(1) == self.f3(1)
            assert unpacked_f3(2) == self.f3(2)
            unpacked_michelson = sp.unpack(
                self.data.lambda_michelson, sp.lambda_[sp.int, sp.int]
            ).unwrap_some()
            assert sp.pack(unpacked_michelson) == sp.pack(
                lambda x: sp.michelson(
                    "DUP; PUSH int 42; ADD; MUL", [sp.int], [sp.int], x
                )
            )
            assert unpacked_michelson(2) == 88

            assert (
                sp.concat(
                    sp.unpack(self.data.list_string, sp.list[sp.string]).unwrap_some()
                )
                == "this is a test"
            )
            m = sp.unpack(
                self.data.map_string_int, sp.map[sp.string, sp.int]
            ).unwrap_some()
            assert m["answer"] == 42 and sp.len(m) == 1
            assert sp.unpack(
                self.data.record_string_int, sp.record(a=sp.string, b=sp.int)
            ).unwrap_some() == sp.record(a="test", b=1337)
            assert sp.unpack(
                self.data.variant_a_string_b_nat, sp.variant(a=sp.string, b=sp.nat)
            ).unwrap_some() == sp.cast(
                sp.variant.a("test"), sp.variant(a=sp.string, b=sp.nat)
            )
            assert sp.unpack(
                self.data.option_string, sp.option[sp.string]
            ).unwrap_some() == sp.Some("hello")
            assert sp.unpack(
                self.data.none_string, sp.option[sp.string]
            ).unwrap_some() == sp.cast(None, sp.option[sp.string])

            # TODO when chain_id creation is implemented
            # assert sp.unpack(self.data.chain_id, sp.chain_id).unwrap_some() == sp.chain_id("NetXnHfVqm9iesp")
            assert sp.unpack(self.data.level_2548242, sp.nat).unwrap_some() == 2548242

            # TODO: activate when sapling is implemented
            # assert sp.unpack(self.data.sapling_transaction, ...).unwrap_some() == ...
            # assert sp.unpack(self.data.sapling_state, ...).unwrap_some() == ...

        @sp.entrypoint
        def pack_lambdas(self):
            f1 = self.f3
            sp.cast(f1, sp.lambda_[sp.int, sp.string])
            p1 = sp.pack(f1)
            f2 = sp.unpack(p1, sp.lambda_[sp.int, sp.string]).unwrap_some()
            p2 = sp.pack(f2)
            assert p1 == p2
            assert f1(0) == f2(0)
            assert f1(1) == f2(1)
            assert f1(2) == f2(2)

        @sp.entrypoint
        def pack_lambdas2(self):
            def f(x):
                return x > 0

            f1 = sp.cast(f, sp.lambda_[int, bool])
            p1 = sp.pack(f1)
            f2 = sp.unpack(p1, sp.lambda_[int, bool]).unwrap_some()
            assert f2(1)

        @sp.entrypoint
        def pack_lambda_record(self):
            f = lambda x: sp.record(a=1, b=x + 2)

            f2 = sp.unpack(
                sp.pack(f), sp.lambda_[int, sp.record(a=int, b=int)]
            ).unwrap_some()
            assert f2(100).a == 1

            g = lambda x: sp.record(a=x + 1)

            g2 = sp.unpack(sp.pack(g), sp.lambda_[int, sp.record(a=int)]).unwrap_some()
            assert g2(100).a == 101

        @sp.entrypoint
        def pack_lambda_variant(self):
            f = lambda x: sp.cast(sp.variant.a(x + 1), tv)
            f2 = sp.unpack(sp.pack(f), t1).unwrap_some()
            assert f2(100).unwrap.a() == 101

            f_ = lambda x: sp.variant.a(x + 1)
            f2_ = sp.unpack(sp.pack(f_), t2).unwrap_some()
            assert f2_(100).unwrap.a() == 101

        @sp.entrypoint
        def pack_unpack_pack_lambda(self):
            assert sp.pack(self.f3) == sp.pack(
                sp.unpack(sp.pack(self.f3), int_to_string).unwrap_some()
            )
            assert sp.pack(
                sp.unpack(sp.pack(self.f3), int_to_string).unwrap_some()
            ) == sp.pack(
                sp.unpack(
                    sp.pack(sp.unpack(sp.pack(self.f3), int_to_string).unwrap_some()),
                    int_to_string,
                ).unwrap_some()
            )


if "main" in __name__:

    @sp.add_test()
    def test():
        sc = sp.test_scenario("Pack")
        c1 = main.Pack()
        sc += c1
        if sc.simulation_mode() is sp.SimulationMode.MOCKUP:
            sc.p("mockups - TODO mockups cant use secret keys")
            return

        signature = sp.make_signature(
            sp.test_account("keystore").secret_key,
            sp.pack("value"),
            message_format="Raw",
        )
        c1.pack(
            signature_sig=sp.signature(
                "sigTBpkXw6tC72L2nJ2r2Jm5iB6uidTWqoMNd4oEawUbGBf5mHVfKawFYL8X8MJECpL73oBnfujyUZNLK2LQWD1FaCkYMP4j"
            ),
            signature_spsig=sp.signature(
                "spsig1PPUFZucuAQybs5wsqsNQ68QNgFaBnVKMFaoZZfi1BtNnuCAWnmL9wVy5HfHkR6AeodjVGxpBVVSYcJKyMURn6K1yknYLm"
            ),
            signature_p2sig=sp.signature(
                "p2sigsceCzcDw2AeYDzUonj4JT341WC9Px4wdhHBxbZcG1FhfqFVuG7f2fGCzrEHSAZgrsrQWpxduDPk9qZRgrpzwJnSHC3gZJ"
            ),
            s=signature,
            _level=2548242,
            _chain_id=sp.chain_id_cst("0xaf1864d9feee0e1f"),
        )
        c1.unpack(
            signature_sig=sp.signature(
                "sigTBpkXw6tC72L2nJ2r2Jm5iB6uidTWqoMNd4oEawUbGBf5mHVfKawFYL8X8MJECpL73oBnfujyUZNLK2LQWD1FaCkYMP4j"
            ),
            signature_spsig=sp.signature(
                "spsig1PPUFZucuAQybs5wsqsNQ68QNgFaBnVKMFaoZZfi1BtNnuCAWnmL9wVy5HfHkR6AeodjVGxpBVVSYcJKyMURn6K1yknYLm"
            ),
            signature_p2sig=sp.signature(
                "p2sigsceCzcDw2AeYDzUonj4JT341WC9Px4wdhHBxbZcG1FhfqFVuG7f2fGCzrEHSAZgrsrQWpxduDPk9qZRgrpzwJnSHC3gZJ"
            ),
            s=signature,
            _level=2548242,
            _chain_id=sp.chain_id_cst("0xaf1864d9feee0e1f"),
        )
        c1.pack_lambdas()
        c1.pack_lambdas2()
        c1.pack_lambda_record()
        c1.pack_lambda_variant()
        c1.pack_unpack_pack_lambda()
