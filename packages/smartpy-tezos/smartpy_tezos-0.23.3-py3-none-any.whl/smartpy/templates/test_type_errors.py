import smartpy as sp


@sp.module
def M():
    def x():
        return 42


@sp.module
def m001():
    _ = sp.cast(42, t)


@sp.module
def m002():
    _ = sp.cast(42, M.t)


@sp.module
def m003():
    _ = sp.cast(42, ABC.t)


@sp.module
def m004():
    x: type = sp.int
    x: type = sp.int


@sp.module
def m005():
    x: type = sp.int
    y = x


@sp.module
def m006():
    y = x


@sp.module
def m007():
    def f():
        pass

    def f():
        pass


@sp.module
def m008():
    def f():
        x = 42
        x = "abc"


@sp.module
def m009():
    _ = sp.create_contract(AB.C, None, sp.mutez(0), ())


@sp.module
def m010():
    def f(x):
        x = 42


@sp.module
def m011():
    x = 42

    def f():
        x = 42


@sp.module
def m012():
    def f(x):
        match (x):
            case A(y):
                y = 42


@sp.module
def m013():
    def f(x):
        (x, y) = (1, 2)


@sp.module
def m014():
    def f():
        _ = sp.create_contract(C, None, sp.mutez(0), ())


@sp.module
def m015():
    def f():
        return 42
        x = 42


@sp.module
def m016():
    class C(sp.Contract):
        @sp.entrypoint
        def ep(self):
            self.__init__(self, 42)


@sp.module
def m017():
    class A(sp.Contract):
        pass

    class C(sp.Contract):
        def __init__(self):
            A.__init__(self)


@sp.module
def m018():
    def f():
        with sp.modify_record(42) as y:
            pass


@sp.module
def m019():
    def f(x):
        match 42:
            case A(y):
                pass


@sp.module
def m020():
    def f(x):
        match sp.variant.A(42):
            case A(y):
                assert y == "abc"


@sp.module
def m021():
    def f():
        with sp.modify_record(42) as y:
            pass


@sp.module
def m022():
    def f(x):
        with sp.modify_record(x) as y:
            return 42


@sp.module
def m023():
    def f():
        42


@sp.module
def m024():
    def f():
        (x, (y, z)) = (3, 4)


@sp.module
def m025():
    def f():
        (x, y) = 3


@sp.module
def m026():
    def f():
        record(a=a, b=b).match = 42


@sp.module
def m027():
    t: type = int

    def f():
        t = 42


@sp.module
def m028():
    def g():
        x = sp.record(a=42)
        x.a = "abc"


@sp.module
def m029():
    def f():
        for x in 42:
            pass


@sp.module
def m030():
    def f():
        if "abc":
            pass


@sp.module
def m031():
    def f():
        while "abc":
            pass


@sp.module
def m032():
    def f():
        sp.cast(42, sp.string)


@sp.module
def m033():
    def f():
        assert 42


@sp.module
def m034():
    def f():
        x = {42}
        x.add("abc")


@sp.module
def m035():
    def f():
        x = {42}
        x.remove("abc")


@sp.module
def m036():
    def f():
        sp.never(42)


@sp.module
def m037():
    class C(sp.Contract):
        @sp.entrypoint
        def ep(self):
            _ = sp.self_entrypoint("abc")


@sp.module
def m038():
    class Fibonacci(sp.Contract):
        def __init__(self):
            self.data.counter = 0
            self.data.steps = []

        @sp.entrypoint
        def run(self, n):
            self.data.steps.push(n)
            if n > 1:
                sp.transfer(n - 2, sp.mutez(0), sp.self_entrypoint("run"))
                sp.transfer(n - 1, sp.mutez(0), sp.self_entrypoint("run"))
            else:
                self.data.counter += 1

        @sp.entrypoint
        def compute(self, n):
            self.data.counter = 0
            self.data.steps = []
            sp.transfer(n, sp.mutez(0), sp.self_entrypoint("run"))


@sp.module
def m039():
    def f():
        _ = abs(True)


@sp.module
def m040():
    def f():
        _ = sp.sub_mutez(1, sp.mutez(2))


@sp.module
def m041():
    def f():
        _ = sp.sub_mutez(sp.mutez(1), 2)


@sp.module
def m042():
    def f(k, s, b):
        sp.cast(k, sp.unit)
        sp.cast(s, sp.signature)
        sp.cast(b, sp.bytes)
        _ = sp.check_signature(k, s, b)


@sp.module
def m042():
    def f(k, s, b):
        sp.cast(k, sp.key)
        sp.cast(s, sp.unit)
        sp.cast(b, sp.bytes)
        _ = sp.check_signature(k, s, b)


@sp.module
def m042():
    def f(k, s, b):
        sp.cast(k, sp.key)
        sp.cast(s, sp.signature)
        sp.cast(b, sp.unit)
        _ = sp.check_signature(k, s, b)


@sp.module
def m043():
    x = sp.sum(["a"])


@sp.module
def m044():
    class C(sp.Contract):
        @sp.entrypoint
        def ep(self):
            sp.set_delegate(42)


@sp.module
def m045():
    _ = sp.unpack(42, int)


@sp.module
def m046():
    _ = sp.implicit_account(42)


@sp.module
def m047():
    _ = sp.to_nat("abc")


@sp.module
def m048():
    _ = [1, "abc"]


@sp.module
def m049():
    def f():
        x = sp.nat(2) / sp.int(-3)


@sp.module
def m050():
    def f():
        x = "abc" / True


@sp.module
def m051():
    def f():
        x = "abc" + 2


@sp.module
def m052():
    def f():
        x = sp.mod("abc", 2)


@sp.module
def m053():
    def f():
        x = sp.mod(sp.nat(1), sp.int(2))


@sp.module
def m054():
    def f():
        pass


@sp.module
def m055():
    def f():
        pass


@sp.module
def m056():
    def f():
        pass


@sp.module
def m057():
    def f():
        pass


@sp.module
def m058():
    def f():
        pass


@sp.module
def m059():
    def f():
        pass


@sp.module
def m060():
    def f():
        pass


@sp.module
def m061():
    def f():
        pass


@sp.module
def m062():
    def f():
        pass


@sp.module
def m063():
    def f():
        pass


@sp.module
def m064():
    def f():
        pass


@sp.module
def m065():
    def f():
        pass


@sp.module
def m066():
    def f():
        pass


@sp.module
def m067():
    def f():
        pass


@sp.module
def m068():
    def f():
        pass


@sp.module
def m069():
    def f():
        pass


@sp.module
def m070():
    def f():
        pass


@sp.module
def m071():
    def f():
        pass


@sp.module
def m072():
    def f():
        pass


@sp.module
def m073():
    def f():
        pass


@sp.module
def m074():
    def f():
        pass


@sp.module
def m075():
    def f():
        pass


@sp.module
def m076():
    def f():
        pass


@sp.module
def m077():
    def f():
        pass


@sp.module
def m078():
    def f():
        pass


@sp.module
def m079():
    def f():
        pass


@sp.module
def m080():
    def f():
        pass


@sp.module
def m081():
    def f():
        pass


@sp.module
def m082():
    def f():
        pass


@sp.module
def m083():
    def f():
        pass


@sp.module
def m084():
    def f():
        pass


@sp.module
def m085():
    def f():
        pass


@sp.module
def m086():
    def f():
        pass


@sp.module
def m087():
    def f():
        pass


@sp.module
def m088():
    def f():
        pass


@sp.module
def m089():
    def f():
        pass


def test_module(s, name, m):
    try:
        s.add_module(m)
    except Exception as e:
        print(name)
        print(e)


@sp.add_test()
def test():
    s = sp.test_scenario("s")
    test_module(s, "m001", m001)
    test_module(s, "m002", m002)
    test_module(s, "m003", m003)
    test_module(s, "m004", m004)
    test_module(s, "m005", m005)
    test_module(s, "m006", m006)
    test_module(s, "m007", m007)
    test_module(s, "m008", m008)
    test_module(s, "m009", m009)

    test_module(s, "m010", m010)
    test_module(s, "m011", m011)
    test_module(s, "m012", m012)
    test_module(s, "m013", m013)
    test_module(s, "m014", m014)
    test_module(s, "m015", m015)
    test_module(s, "m016", m016)
    test_module(s, "m017", m017)
    test_module(s, "m018", m018)
    test_module(s, "m019", m019)

    test_module(s, "m020", m020)
    test_module(s, "m021", m021)
    test_module(s, "m022", m022)
    test_module(s, "m023", m023)
    test_module(s, "m024", m024)
    test_module(s, "m025", m025)
    test_module(s, "m026", m026)
    test_module(s, "m027", m027)
    test_module(s, "m028", m028)
    test_module(s, "m029", m029)

    test_module(s, "m030", m030)
    test_module(s, "m031", m031)
    test_module(s, "m032", m032)
    test_module(s, "m033", m033)
    test_module(s, "m034", m034)
    test_module(s, "m035", m035)
    test_module(s, "m036", m036)
    test_module(s, "m037", m037)
    test_module(s, "m038", m038)
    test_module(s, "m039", m039)

    test_module(s, "m040", m040)
    test_module(s, "m041", m041)
    test_module(s, "m042", m042)
    test_module(s, "m043", m043)
    test_module(s, "m044", m044)
    test_module(s, "m045", m045)
    test_module(s, "m046", m046)
    test_module(s, "m047", m047)
    test_module(s, "m048", m048)
    test_module(s, "m049", m049)

    test_module(s, "m050", m050)
    test_module(s, "m051", m051)
    test_module(s, "m052", m052)
    test_module(s, "m053", m053)
    test_module(s, "m054", m054)
    test_module(s, "m055", m055)
    test_module(s, "m056", m056)
    test_module(s, "m057", m057)
    test_module(s, "m058", m058)
    test_module(s, "m059", m059)

    test_module(s, "m060", m060)
    test_module(s, "m061", m061)
    test_module(s, "m062", m062)
    test_module(s, "m063", m063)
    test_module(s, "m064", m064)
    test_module(s, "m065", m065)
    test_module(s, "m066", m066)
    test_module(s, "m067", m067)
    test_module(s, "m068", m068)
    test_module(s, "m069", m069)

    test_module(s, "m070", m070)
    test_module(s, "m071", m071)
    test_module(s, "m072", m072)
    test_module(s, "m073", m073)
    test_module(s, "m074", m074)
    test_module(s, "m075", m075)
    test_module(s, "m076", m076)
    test_module(s, "m077", m077)
    test_module(s, "m078", m078)
    test_module(s, "m079", m079)

    test_module(s, "m080", m080)
    test_module(s, "m081", m081)
    test_module(s, "m082", m082)
    test_module(s, "m083", m083)
    test_module(s, "m084", m084)
    test_module(s, "m085", m085)
    test_module(s, "m086", m086)
    test_module(s, "m087", m087)
    test_module(s, "m088", m088)
    test_module(s, "m089", m089)
