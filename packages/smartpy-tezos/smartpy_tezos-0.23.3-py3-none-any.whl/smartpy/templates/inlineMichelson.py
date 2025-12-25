import smartpy as sp


@sp.module
def main():
    class C(sp.Contract):
        def __init__(self):
            self.data.value = 0
            self.data.s = ""

        @sp.entrypoint
        def arith(self):
            assert sp.michelson("ADD", [int, int], [int], 1, 2) == 3
            assert sp.michelson("ADD", [int, int], [int], 1, -2) == -1

            assert sp.michelson("SUB", [int, int], [int], 1, -2) == 3
            assert sp.michelson("SUB", [int, int], [int], 1, 2) == -1

        @sp.entrypoint
        def prim0(self):
            assert sp.michelson("UNIT", [], [sp.unit]) == ()

            assert sp.michelson("NONE unit", [], [sp.option[sp.unit]]) == None

            assert sp.michelson(
                "PUSH int 2; PUSH int 1; PAIR", [], [sp.pair[int, int]]
            ) == (1, 2)

            assert sp.len(sp.michelson("NIL unit", [], [list[sp.unit]])) == 0

            assert sp.len(sp.michelson("EMPTY_SET unit", [], [set[sp.unit]])) == 0

            assert (
                sp.len(sp.michelson("EMPTY_MAP unit unit", [], [map[sp.unit, sp.unit]]))
                == 0
            )

            # assert sp.len(michelson("EMPTY_BIG_MAP unit unit", [], [bigmap[unit, unit]])) == 0)

        @sp.entrypoint
        def overflow_add(self):
            _ = sp.michelson(
                "ADD",
                [sp.mutez, sp.mutez],
                [sp.mutez],
                sp.mutez(9223372036854775807),
                sp.mutez(1),
            )

        @sp.entrypoint
        def overflow_mul(self):
            _ = sp.michelson(
                "MUL", [sp.mutez, sp.nat], [sp.mutez], sp.mutez(4611686018427387904), 2
            )

        @sp.entrypoint
        def underflow(self):
            assert (
                sp.michelson(
                    "SUB_MUTEZ",
                    [sp.mutez, sp.mutez],
                    [sp.option[sp.mutez]],
                    sp.mutez(0),
                    sp.mutez(1),
                )
                == None
            )

        @sp.entrypoint
        def concat1(self):
            assert (
                sp.michelson("CONCAT", [list[sp.string]], [sp.string], ["a", "b", "c"])
                == "abc"
            )

        @sp.entrypoint
        def concat2(self):
            assert (
                sp.michelson("CONCAT", [sp.string, sp.string], [sp.string], "a", "b")
                == "ab"
            )

        @sp.entrypoint
        def seq(self):
            assert (
                sp.michelson(
                    "DIP {SWAP}; ADD; MUL; DUP; MUL;",
                    [int, int, int],
                    [int],
                    15,
                    16,
                    17,
                )
                == 262144
            )

        @sp.entrypoint
        def lambdas(self):
            assert (
                sp.michelson(
                    "PUSH (lambda int int) {DUP; ADD}; SWAP; EXEC;", [int], [int], 100
                )
                == 200
            )

            # f = michelson("PUSH (lambda (pair int int) int) {UNPAIR; PUSH int 10; MUL; ADD;}; SWAP; EXEC;", [int, int], [int])
            # assert f(2,5) == 25
            # TODO Why does this not fail during type checking?

            assert (
                sp.michelson(
                    "PAIR; PUSH (lambda (pair int int) int) { UNPAIR; PUSH int 10; MUL; ADD;}; SWAP; EXEC;",
                    [int, int],
                    [int],
                    2,
                    5,
                )
                == 25
            )

            assert (
                sp.michelson(
                    "PAIR 3; PUSH (lambda (pair int int int) int) { UNPAIR 3; PUSH int 10; MUL; ADD; PUSH int 10; MUL; ADD;}; SWAP; EXEC;",
                    [int, int, int],
                    [int],
                    2,
                    5,
                    7,
                )
                == 257
            )

            assert (
                sp.michelson(
                    "PUSH (lambda (pair int int int) int) { UNPAIR 3; PUSH int 10; MUL; ADD; PUSH int 10; MUL; ADD;}; PUSH int 2; APPLY; PUSH int 5; APPLY; PUSH int 7; EXEC;",
                    [],
                    [int],
                )
                == 257
            )

            # TODO lambda that traverses the SmartPy-Michelson barrier

            assert (
                sp.michelson(
                    "LAMBDA_REC int int                { DUP; PUSH int 1; COMPARE; GE; IF { DROP 2; PUSH int 1; } { DUP; PUSH int 1; SWAP; SUB; DIG 2; SWAP; EXEC; MUL; }; }; SWAP; EXEC;",
                    [int],
                    [int],
                    5,
                )
                == 120
            )

            assert (
                sp.michelson(
                    "PUSH (lambda int int) (Lambda_rec { DUP; PUSH int 1; COMPARE; GE; IF { DROP 2; PUSH int 1; } { DUP; PUSH int 1; SWAP; SUB; DIG 2; SWAP; EXEC; MUL; }; }); SWAP; EXEC;",
                    [int],
                    [int],
                    5,
                )
                == 120
            )

        @sp.entrypoint
        def test_operations(self):
            op1 = sp.michelson("NONE key_hash; SET_DELEGATE;", [], [sp.operation])
            sp.operations.push(op1)

            c = sp.michelson(
                "PUSH int 123; PUSH mutez 0; NONE key_hash; CREATE_CONTRACT { parameter int; storage int; code { UNPAIR; ADD; NIL operation; PAIR } }; PAIR",
                [],
                [sp.pair[sp.operation, sp.address]],
            )
            (op, address) = c
            sp.operations.push(sp.fst(c))


@sp.add_test()
def test():
    scenario = sp.test_scenario("Inline Michelson")
    c = main.C()
    scenario += c
    c.prim0()
    c.arith()
    c.overflow_add(_valid=False, _exception="ADD: mutez overflow")
    c.overflow_mul(_valid=False, _exception="MUL: mutez overflow")
    c.underflow()
    c.seq()
    c.lambdas()
    c.test_operations()
