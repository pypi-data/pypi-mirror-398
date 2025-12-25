from ..internal import sexp
from ..internal.base import BaseExpr, BaseTypeRef
from ..internal.state import get_state
from ..internal.utils import get_file_line_no, pretty_line_no

pyRange = range
pyBool = bool
pyInt = int
pySet = set
pyList = list
pyTuple = tuple
pyBytes = bytes
pyMap = map
pyLen = len


def of_hole(f, x):
    return sexp.Atom("Variable") if x is None else sexp.List("Value", f(x))


class _Unit:
    pass


class WouldBeValue:
    def __repr__(self):
        try:
            return self.export()
        except:
            return "value of type %s. %s" % (
                self.__class__.__name__,
                pretty_line_no(),
            )

    def __iter__(self):
        raise Exception(
            f"Non iterable object from Python. Please use scenario.verify_equal if you want to assert the equality of two values. {self.export()}"
        )


def unknown():
    get_state().unknownIds += 1
    return TUnknown(get_state().unknownIds)


def conv(t):
    if isinstance(t, WouldBeValue):
        raise Exception("Bad type expression " + str(t))
    if isinstance(t, _Unit):
        return TUnit
    if t is None:
        t = unknown()
    # This line needs to come before lines with ==.
    if isinstance(t, TType):
        return t
    if isinstance(t, BaseTypeRef):
        return t
    if isinstance(t, BaseExpr):
        raise Exception("Expression cannot be used as a type: " + str(t))
    if t == pyInt:
        raise Exception("Type int in this context is referred to as sp.int.")
    if t == pyBool:
        raise Exception("Type bool in this context is referred to as sp.bool.")
    if t == str:
        raise Exception("Type str in this context is referred to as sp.str.")
    if t == pyBytes:
        raise Exception("Type bytes in this context is referred to as sp.bytes.")
    if isinstance(t, pyList) and pyLen(t) == 1:
        return TList(conv(t[0]))
    if isinstance(t, type):
        raise Exception(f"Type {t.__qualname__} is incomplete.")

    raise Exception("Bad type expression " + str(t) + " of type " + str(type(t)))


class TType:
    def __repr__(self):
        return self.export()


class TRecord(TType):
    def __init__(self, **kargs):
        args = {}
        for k, v in kargs.items():
            v = conv(v)
            args[k] = v
            setattr(self, k, v)
        self.kargs = args
        self.layout_ = None
        self.line_no = get_file_line_no().export()

    def layout(self, layout):
        result = TRecord(**dict(self.kargs))
        result.layout_ = parse_layout(layout)
        return result

    def right_comb(self):
        result = TRecord(**dict(self.kargs))
        result.layout_ = "right_comb"
        return result

    def with_fields(self, **kargs):
        result = dict(self.kargs)
        for k, v in kargs.items():
            result[k] = v
        return TRecord(**result)

    def without_fields(self, l):
        result = dict(self.kargs)
        for k in l:
            del result[k]
        return TRecord(**result)

    def export(self):
        fields = " ".join(
            "(%s %s)" % (x, y.export()) for (x, y) in sorted(self.kargs.items())
        )
        layout = ("(Value %s)" % self.layout_) if self.layout_ else "Variable"
        return "(record (%s) %s %s)" % (fields, layout, self.line_no)


def parse_layout(layout):
    if isinstance(layout, tuple):
        if len(layout) != 2:
            raise Exception("Layout computation on non-pair %s" % (str(layout)))
        return "(%s %s)" % (parse_layout(layout[0]), parse_layout(layout[1]))
    if isinstance(layout, str):
        return '("%s")' % layout
    raise Exception("Layout computation on non-pair or str %s" % (str(layout)))


class TVariant(TType):
    def __init__(self, **kargs):
        args = sorted(kargs.items())
        self.kargs = kargs
        self.layout_ = None
        for k, v in args:
            setattr(self, k, conv(v))
        self.line_no = get_file_line_no().export()

    def layout(self, layout):
        self.layout_ = parse_layout(layout)
        return self

    def right_comb(self):
        self.layout_ = "right_comb"
        return self

    def export(self):
        fields = " ".join(
            "(%s %s)" % (x, y.export()) for (x, y) in sorted(self.kargs.items())
        )
        layout = ("(Value %s)" % self.layout_) if self.layout_ else "Variable"
        return "(variant (%s) %s %s)" % (fields, layout, self.line_no)


def TOr(tleft, tright):
    return TVariant(Left=tleft, Right=tright)


class TSimple(TType):
    def __init__(self, name):
        self.name = name

    def export(self):
        return '"%s"' % self.name


class TSaplingState(TType):
    def __init__(self, memo_size=None):
        self.name = "sapling_state"
        self.memo_size = of_hole(sexp.of_int, memo_size)

    def export(self):
        return "(%s %s)" % (self.name, self.memo_size)


class TSaplingTransaction(TType):
    def __init__(self, memo_size=None):
        self.name = "sapling_transaction"
        self.memo_size = of_hole(sexp.of_int, memo_size)

    def export(self):
        return "(%s %s)" % (self.name, str(self.memo_size))


TUnit = TSimple("unit")
TBool = TSimple("bool")
TInt = TSimple("int")
TNat = TSimple("nat")
TIntOrNat = TSimple("int_or_nat")
TString = TSimple("string")
TBytes = TSimple("bytes")
TMutez = TSimple("mutez")
TTimestamp = TSimple("timestamp")
TAddress = TSimple("address")
TKey = TSimple("key")
TSecretKey = TSimple("secret_key")
TKeyHash = TSimple("key_hash")
TSignature = TSimple("signature")
TChainId = TSimple("chain_id")
TBls12_381_g1 = TSimple("bls12_381_g1")  # Points on the BLS12-381 curve G1
TBls12_381_g2 = TSimple("bls12_381_g2")  # Points on the BLS12-381 curve G2
TBls12_381_fr = TSimple(
    "bls12_381_fr"
)  # An element of the scalar field Fr, used for scalar multiplication on the BLS12-381 curves G1 and G2.
TChest_key = TSimple(
    "chest_key"
)  # Represents the decryption key, alongside with a proof that the key is correct.
TChest = TSimple(
    "chest"
)  # Represents timelocked arbitrary bytes with the necessary public parameters to open it.
TNever = TSimple("never")


class TUnknown(TType):
    def __init__(self, id):
        self.id = id

    def export(self):
        return "(unknown %i)" % self.id


class TList(TType):
    def __init__(self, t):
        self.t = conv(t)

    def export(self):
        return "(list %s)" % self.t.export()


class TTicket(TType):
    def __init__(self, t):
        self.t = conv(t)

    def export(self):
        return "(ticket %s)" % self.t.export()


class TMap(TType):
    def __init__(self, k, v):
        self.k = conv(k)
        self.v = conv(v)

    def export(self):
        return "(map %s %s)" % (self.k.export(), self.v.export())


class TSet(TType):
    def __init__(self, t):
        self.t = conv(t)

    def export(self):
        return "(set %s)" % self.t.export()


class TBigMap(TType):
    def __init__(self, k, v):
        self.k = conv(k)
        self.v = conv(v)

    def export(self):
        return "(big_map %s %s)" % (self.k.export(), self.v.export())


class TPair(TType):
    def __init__(self, t1, t2):
        self.t1 = t1
        self.t2 = t2

    def export(self):
        return "(tuple %s %s)" % (
            conv(self.t1).export(),
            conv(self.t2).export(),
        )


class TTuple(TType):
    def __init__(self, *args):
        self.types = args

    def export(self):
        return "(tuple %s)" % (" ".join([conv(i).export() for i in self.types]))


class TAnnots(TType):
    def __init__(self, t, *annots):
        self.t = conv(t)
        self.annots = annots

    def export(self):
        return "(annots %s (%s))" % (
            self.t.export(),
            " ".join('"%s"' % a for a in self.annots),
        )


class TOption(TType):
    def __init__(self, t):
        self.t = conv(t)

    def export(self):
        return "(option %s)" % self.t.export()


class TContract(TType):
    def __init__(self, t):
        self.t = conv(t)

    def export(self):
        return "(contract %s)" % self.t.export()


class TLambda(TType):
    def __init__(
        self,
        t1,
        t2,
        with_storage=None,
        with_operations=None,
        with_exceptions=None,
        with_mutez_overflow=None,
        with_mutez_underflow=None,
        tstorage=None,
    ):
        self.t1 = conv(t1)
        self.t2 = conv(t2)
        self.with_storage = with_storage
        self.with_operations = with_operations
        self.with_exceptions = with_exceptions
        self.with_mutez_overflow = with_mutez_overflow
        self.with_mutez_underflow = with_mutez_underflow
        self.tstorage = tstorage
        if with_storage is None and tstorage is not None:
            raise Exception("Cannot specify tstorage without setting with_storage.")
        if self.with_storage not in [None, "read-write", "read-only"]:
            raise Exception(
                'with_storage parameter can only be None, "read-only" or "read-write".'
            )

    def export(self):
        tstorage = "None" if self.tstorage is None else self.tstorage.export()
        with_operations = (
            "None"
            if self.with_operations is None
            else sexp.of_bool(self.with_operations)
        )
        with_exceptions = (
            "None"
            if self.with_exceptions is None
            else sexp.of_bool(self.with_exceptions)
        )
        with_mutez_overflow = (
            "None"
            if self.with_mutez_overflow is None
            else sexp.of_bool(self.with_mutez_overflow)
        )
        with_mutez_underflow = (
            "None"
            if self.with_mutez_underflow is None
            else sexp.of_bool(self.with_mutez_underflow)
        )
        with_storage = (
            "None" if self.with_storage is None else sexp.Atom(self.with_storage)
        )
        return "(lambda %s %s %s %s %s %s %s %s)" % (
            with_storage,
            with_operations,
            with_exceptions,
            with_mutez_overflow,
            with_mutez_underflow,
            tstorage,
            self.t1.export(),
            self.t2.export(),
        )
