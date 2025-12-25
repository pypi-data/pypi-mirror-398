import smartpy as sp


@sp.module
def main():
    class C(sp.Contract):
        def __init__(self):
            self.data.xy = (0, 0)

        @sp.entrypoint
        def ep1(self):
            self.data.xy = (sp.snd(self.data.xy), sp.fst(self.data.xy))

        @sp.entrypoint
        def ep2(self):
            self.data.xy = (
                sp.snd(sp.fst((self.data, ())).xy),
                sp.fst(sp.fst((self.data, ())).xy),
            )

        @sp.entrypoint
        def ep3(self):
            self.data.xy = (sp.fst(self.data.xy), sp.fst(self.data.xy))

        @sp.entrypoint
        def ep4(self):
            self.data.xy = (sp.snd(self.data.xy), sp.snd(self.data.xy))

        @sp.entrypoint
        def ep5(self, params):
            sp.cast(params, sp.nat)
            match sp.ediv(params, 2):
                case None:
                    self.data.xy = (0, 0)
                case Some(s65):
                    self.data.xy = (1, 1)

        @sp.entrypoint
        def ep6(self, params):
            sp.cast(params, sp.nat)
            match sp.ediv(params, 2):
                case Some(s65):
                    self.data.xy = (1, 1)
                case None:
                    self.data.xy = (0, 0)


@sp.add_test()
def test():
    scenario = sp.test_scenario("Misc")
    scenario += main.C()
