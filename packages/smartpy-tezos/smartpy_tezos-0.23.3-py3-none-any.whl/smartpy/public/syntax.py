import datetime
from types import FunctionType

import smartpy.internal.sexp as sexp
from smartpy.internal.base import BaseExpr, BaseParsedExpr, BaseRef, BaseTestAccount
from smartpy.internal.utils import (
    LineNo,
    get_file_line_no,
    get_id_from_line_no,
    pretty_line_no,
)
from smartpy.platform.services import ParseKind, parse_via_exe_or_js
from smartpy.public.metadata import InstanceOffchainViewsMetadata
from smartpy.public.types import *
from smartpy.public.types import TType, _Unit

_hex_digits = pySet("0123456789abcdefABCDEF")


def of_hole(f, x):
    return sexp.Atom("Variable") if x is None else sexp.List("Value", f(x))


class Helpers:
    @staticmethod
    def areBytesValid(x):
        return (
            isinstance(x, str)
            and x.startswith("0x")
            and all(c in _hex_digits for c in x[2:])
            and pyLen(x) % 2 == 0
        )


class Expr(BaseExpr):
    def __init__(self, f, l, line_no=None):
        self.line_no = line_no
        self._f = f
        self._l = l
        self.opens = {}
        self.unwrap_variant = self.UnwrapVariant(self)
        setattr(self, "__initialized", True)

    class UnwrapVariant:
        def __init__(self, outer_instance):
            self.outer_instance = outer_instance

        def __getattr__(self, name):
            return lambda error=None: self.outer_instance.open_variant(
                name, message=error
            )

    def __eq__(self, other):
        return Expr("eq", [self, spExpr(other)], get_file_line_no())

    def __ne__(self, other):
        return Expr("neq", [self, spExpr(other)], get_file_line_no())

    def __add__(self, other):
        return Expr("add_homo", [self, spExpr(other)], get_file_line_no())

    def __sub__(self, other):
        return Expr("sub", [self, spExpr(other)], get_file_line_no())

    def __mul__(self, other):
        return Expr("mul_homo", [self, spExpr(other)], get_file_line_no())

    def __mod__(self, other):
        return Expr("mod", [self, spExpr(other)], get_file_line_no())

    def __truediv__(self, other):
        return Expr("div", [self, spExpr(other)], get_file_line_no())

    def __floordiv__(self, other):
        return Expr("div", [self, spExpr(other)], get_file_line_no())

    def __rtruediv__(self, other):
        return Expr("div", [spExpr(other), self], get_file_line_no())

    def __rfloordiv__(self, other):
        return Expr("div", [spExpr(other), self], get_file_line_no())

    def __radd__(self, other):
        return Expr("add_homo", [spExpr(other), self], get_file_line_no())

    def __rmul__(self, other):
        return Expr("mul_homo", [spExpr(other), self], get_file_line_no())

    def __rsub__(self, other):
        return Expr("sub", [spExpr(other), self], get_file_line_no())

    def __lt__(self, other):
        return Expr("lt", [self, spExpr(other)], get_file_line_no())

    def __le__(self, other):
        return Expr("le", [self, spExpr(other)], get_file_line_no())

    def __gt__(self, other):
        return Expr("gt", [self, spExpr(other)], get_file_line_no())

    def __ge__(self, other):
        return Expr("ge", [self, spExpr(other)], get_file_line_no())

    def __or__(self, other):
        return Expr("or", [self, spExpr(other)], get_file_line_no())

    def __ror__(self, other):
        return Expr("or", [spExpr(other), self], get_file_line_no())

    def __xor__(self, other):
        return Expr("xor", [self, spExpr(other)], get_file_line_no())

    def __rxor__(self, other):
        return Expr("xor", [spExpr(other), self], get_file_line_no())

    def __and__(self, other):
        return Expr("and", [self, spExpr(other)], get_file_line_no())

    def __rand__(self, other):
        return Expr("and", [spExpr(other), self], get_file_line_no())

    def __lshift__(self, other):
        return Expr("lsl", [self, spExpr(other)], get_file_line_no())

    def __rlshift__(self, other):
        return Expr("lsl", [spExpr(other), self], get_file_line_no())

    def __rshift__(self, other):
        return Expr("lsr", [self, spExpr(other)], get_file_line_no())

    def __rrshift__(self, other):
        return Expr("lsr", [spExpr(other), self], get_file_line_no())

    def __getitem__(self, item):
        return Expr("get_item", [self, spExpr(item)], get_file_line_no())

    def __abs__(self):
        return Expr("abs", [self], get_file_line_no())

    def __neg__(self):
        return Expr("neg", [self], get_file_line_no())

    def __invert__(self):
        return Expr("not", [self], get_file_line_no())

    def __bool__(self):
        self.__nonzero__()

    def __nonzero__(self):
        raise Exception(
            "Cannot convert expression to bool. Conditionals are forbidden on contract expressions."
        )

    def __hash__(self):
        return hash(self.export())

    def get(self, item, default_value=None, message=None):
        if default_value is not None:
            return Expr(
                "get_item_default",
                [self, spExpr(item), spExpr(default_value)],
                get_file_line_no(),
            )
        if message is not None:
            return Expr(
                "get_item_message",
                [self, spExpr(item), spExpr(message)],
                get_file_line_no(),
            )
        return self.__getitem__(item)

    def get_opt(self, key):
        return Expr("get_opt", [self, spExpr(key)], get_file_line_no())

    def __enter__(self):
        return getattr(self, "__asBlock").__enter__()

    def __exit__(self, type, value, traceback):
        getattr(self, "__asBlock").__exit__(type, value, traceback)

    def __iter__(self):
        raise Exception(
            f"Non iterable object from Python. Please use scenario.verify_equal if you want to assert the equality of two expressions. {self.export()}"
        )

    def contains(self, value):
        return Expr("contains", [self, spExpr(value)], get_file_line_no())

    def __contains__(self, value):
        raise Exception(
            "Instead of using expressions such as e1 in e2, please use e2.contains(e1)."
        )

    def __call__(self, arg):
        return Expr("call", [self, spExpr(arg)], get_file_line_no())

    def apply(self, arg):
        return Expr("apply", [spExpr(arg), self], get_file_line_no())

    def __getattr__(self, attr):
        if "__" in attr:
            raise AttributeError("")
        return Expr("attr", [self, attr], get_file_line_no())

    def __setattr__(self, attr, value):
        if "__" not in attr and hasattr(self, "__initialized"):
            set_var(getattr(self, attr), value)
        else:
            object.__setattr__(self, attr, value)

    def __delitem__(self, item):
        raise Exception("Cannot delete item from expression")

    def __setitem__(self, item, value):
        set_var(self[item], value)

    def items(self):
        return Expr("items", [self], get_file_line_no())

    def keys(self):
        return Expr("keys", [self], get_file_line_no())

    def values(self):
        return Expr("values", [self], get_file_line_no())

    def elements(self):
        return Expr("elements", [self], get_file_line_no())

    def rev(self):
        return Expr("rev", [self], get_file_line_no())

    def set(self, other):
        set_var(self, spExpr(other))

    def __repr__(self):
        return self.export()

    def is_none(self):
        return self.is_variant("None")

    def is_some(self):
        return self.is_variant("Some")

    def is_left(self):
        return self.is_variant("Left")

    def is_right(self):
        return self.is_variant("Right")

    def is_variant(self, name):
        return Expr("is_variant", [self, name], get_file_line_no())

    def open_some(self, message=None):
        return self.open_variant("Some", message=message)

    def unwrap_some(self, error=None):
        return self.open_variant("Some", message=error)

    def open_variant(self, name, message=None):
        if message is None:
            try:
                return self.opens[name]
            except KeyError:
                result = Expr(
                    "open_variant",
                    [self, name, "None" if message is None else spExpr(message)],
                    get_file_line_no(),
                )
                self.opens[name] = result
                return result
        else:
            return Expr(
                "open_variant",
                [self, name, "None" if message is None else spExpr(message)],
                get_file_line_no(),
            )

    def push(self, other):
        return set_var(self, cons(spExpr(other), self))

    def map(self, f):
        return Expr("map_function", [self, spExpr(f)], get_file_line_no())

    def add_seconds(self, seconds):
        return Expr("add_seconds", [self, spExpr(seconds)], get_file_line_no())

    def add_minutes(self, minutes):
        return Expr("add_seconds", [self, spExpr(minutes * 60)], get_file_line_no())

    def add_hours(self, hours):
        return Expr(
            "add_seconds", [self, spExpr(hours * (60 * 60))], get_file_line_no()
        )

    def add_days(self, days):
        return Expr(
            "add_seconds", [self, spExpr(days * (24 * 60 * 60))], get_file_line_no()
        )

    def export(self):
        def ppe(e):
            if hasattr(e, "export"):
                return e.export()
            if isinstance(e, str):
                return '"%s"' % e
            return str(e)

        line_no = (
            ""
            if self.line_no is None
            else (
                '("no location info" -1) '
                if self.line_no.line_no == -1
                else "%s " % self.line_no.export()
            )
        )
        if self._f == "invalid":
            raise Exception(" ".join(str(x) for x in self._l))
        if self._l:
            return "(%s%s %s)" % (line_no, self._f, " ".join(ppe(x) for x in self._l))
        return "(%s%s)" % (line_no, self._f)


def name_of_type(t):
    a = str(t).replace("<", "").replace(">", "")
    return a or t.__name__


def literal(t, l, pyType, f_name=None):
    f_name = f_name if f_name else t
    if not name_of_type(type(l)) == name_of_type(pyType):
        raise ValueError(
            "sp.%s(..) awaits a %s and got '%s' of type %s. %s"
            % (
                f_name,
                name_of_type(pyType),
                str(l),
                name_of_type(type(l)),
                pretty_line_no(),
            )
        )
    if t in ["nat", "int_or_nat", "tez", "mutez"] and l < 0:
        raise ValueError(
            "sp.%s(..) cannot contain a negative value and got '%s'. %s"
            % (f_name, str(l), pretty_line_no())
        )

    return Expr("literal", [Expr(t, [l])], get_file_line_no())


def key_hash(s):
    return literal("key_hash", s, str)


unit_ = Expr("literal", [Expr("unit", [])], LineNo("", -1))


def chain_id_cst(x):
    if Helpers.areBytesValid(x):
        return literal("chain_id_cst", x, str)
    raise Exception(
        "sp.chain_id_cst('0x...') awaits a string in hexadecimal format and got '%s'. %s"
        % (str(x), pretty_line_no())
    )


def some(x):
    return Expr("variant", ["Some", spExpr(x)], get_file_line_no())


def Some(x):
    return Expr("variant", ["Some", spExpr(x)], get_file_line_no())


def left(x):
    return Expr("variant", ["Left", spExpr(x)], get_file_line_no())


def right(x):
    return Expr("variant", ["Right", spExpr(x)], get_file_line_no())


def tez(x):
    if isinstance(x, pyInt):
        return literal("mutez", 1000000 * x, pyInt, "tez")
    else:
        raise ValueError(
            "sp.tez(..) is for literals and awaits a python integers and got '%s' of type %s. %s\n\
Please use utils.nat_to_tez to convert a sp.nat expression into a sp.mutez expression."
            % (str(x), name_of_type(type(x)), pretty_line_no())
        )


def secret_key(s):
    return literal("secret_key", s, str)


""" + Timelock Feature """

# Literals


def chest_key(raw_bytes):
    if Helpers.areBytesValid(raw_bytes):
        return literal("chest_key", raw_bytes, str)

    raise Exception(
        "sp.chest_key('0x...') awaits a string in hexadecimal format and got '%s'. %s"
        % (str(raw_bytes), pretty_line_no())
    )


def chest(raw_bytes):
    if Helpers.areBytesValid(raw_bytes):
        return literal("chest", raw_bytes, str)

    raise Exception(
        "sp.chest('0x...') awaits a string in hexadecimal format and got '%s'. %s"
        % (str(raw_bytes), pretty_line_no())
    )


# Instructions

"""
    Opens a timelocked chest given its key and the time.

    The results can be bytes if the opening is correct, or a boolean indicating whether
    the chest was incorrect, or its opening was. See Timelock for more information.

    Arguments:
        chest_key : TChest_key
        chest : TChest
        time : TNat (time in seconds)
"""


def open_chest(chest_key, chest, time):
    return Expr(
        "open_chest",
        [spExpr(chest_key), spExpr(chest), spExpr(time)],
        get_file_line_no(),
    )


""" - Timelock Feature """


"""
* bls12_381_g1 and bls12_381_g2 are written as their raw bytes, using a big-endian point encoding, as specified here.
* bls12_381_fr is written in raw bytes, using a little-endian encoding.

bls12-381 Serialization: https://docs.rs/bls12_381/0.3.1/bls12_381/notes/serialization/index.html#bls12-381-serialization
"""


def bls12_381_g1(raw_bytes):
    if Helpers.areBytesValid(raw_bytes):
        return literal("bls12_381_g1", raw_bytes, str)

    raise Exception(
        "sp.bls12_381_g1('0x...') awaits a string in hexadecimal format and got '%s'. %s"
        % (str(raw_bytes), pretty_line_no())
    )


def bls12_381_g2(raw_bytes):
    if Helpers.areBytesValid(raw_bytes):
        return literal("bls12_381_g2", raw_bytes, str)

    raise Exception(
        "sp.bls12_381_g2('0x...') awaits a string in hexadecimal format and got '%s'. %s"
        % (str(raw_bytes), pretty_line_no())
    )


def bls12_381_fr(raw_bytes):
    if Helpers.areBytesValid(raw_bytes):
        return literal("bls12_381_fr", raw_bytes, str)

    raise Exception(
        "sp.bls12_381_fr('0x...') awaits a string in hexadecimal format and got '%s'. %s"
        % (str(raw_bytes), pretty_line_no())
    )


def pairing_check(pairs):
    return Expr("pairing_check", [spExpr(pairs)], get_file_line_no())


def hash_key(x):
    return Expr("hash_key", [spExpr(x)], get_file_line_no())


def spMetaExpr(x, context="expression"):
    if x is None:
        raise Exception(
            "Unexpected value (None) for %s. %s" % (context, pretty_line_no())
        )
    if isinstance(x, dict):
        return Expr(
            "meta_map",
            [get_file_line_no()]
            + [Expr("elem", [spExpr(k), spMetaExpr(v)]) for (k, v) in x.items()],
        )
    if isinstance(x, pyList):
        return Expr("meta_list", [get_file_line_no()] + [spMetaExpr(y) for y in x])
    return Expr("meta_expr", [spExpr(x)])


def spExpr(x, context="expression"):
    if x is None:
        return none
    if isinstance(
        x,
        (
            Expr,
            BaseRef,
            BaseParsedExpr,
            WouldBeValue,
            ContractTyped,
        ),
    ):
        return x
    if isinstance(x, _Unit) or x == ():
        return unit_
    if isinstance(x, float):
        raise ValueError(
            "Expression cannot be a float. Got '%s'. %s" % (str(x), pretty_line_no())
        )
    if isinstance(x, pyBool):
        return literal("bool", x, pyBool)
    if isinstance(x, pyInt):
        if x < 0:
            return literal("int", x, pyInt)
        return literal("int_or_nat", x, pyInt)
    if hasattr(x, "__int__"):
        return literal("int_or_nat", pyInt(x), pyInt)
    if isinstance(x, str):
        return literal("string", x, str)
    if isinstance(x, pyBytes):
        return literal("bytes", x.decode(), str)
    if isinstance(x, dict):
        return map(x)
    if isinstance(x, pySet):
        x = sorted(x) if all(isinstance(y, pyInt) for y in x) else x
        return set([spExpr(y) for y in x])
    if isinstance(x, pyTuple):
        return tuple_([spExpr(y) for y in x])
    if isinstance(x, pyList):
        return list([spExpr(y) for y in x])
    if isinstance(x, pyRange):
        return list(pyList(x))
    if isinstance(x, FunctionType):
        raise Exception(
            "spExpr: Using Python function is not supported, please defined them in SmartPy modules."
        )
    if isinstance(x, BaseTestAccount):
        return x.e
    if isinstance(x, TType):
        raise Exception("spExpr: using type expression %s as an expression" % (str(x)))
    export_string = ""
    try:
        export_string = " with export = '%s'" % x.export()
    except:
        pass
    raise Exception(
        "No conversion to sp.Expr found for '%s' of type '%s'%s. %s"
        % (str(x), name_of_type(x), export_string, pretty_line_no())
    )


def set_var(var, value):
    if value is None:
        raise Exception("None value for ", var)
    assert pyLen(var._l) > 0
    assert var._l[0]._f == "contract_data"
    return get_state().current_scenario.action(
        {
            "action": "setContractData",
            "line_no": get_file_line_no().export(),
            "rhs": spExpr(value).export(),
            "lhs": var.export(),
        }
    )


def cons(x, xs):
    return Expr("cons", [spExpr(x), spExpr(xs)], get_file_line_no())


# sp.sign is already taken by the sign as in plus or minus
def make_signature(secret_key, message, message_format="Raw"):
    return Expr(
        "make_signature",
        [spExpr(secret_key), spExpr(message), message_format],
        get_file_line_no(),
    )


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


class record_(WouldBeValue):
    def __init__(self, **fields):
        self.fields = {k: spExpr(v) for (k, v) in fields.items()}
        for k, v in self.fields.items():
            setattr(self, k, v)
        self.line_no = get_file_line_no()

    def export(self):
        return "(%s record %s)" % (
            self.line_no.export(),
            " ".join(
                "(%s %s)" % (k, v.export()) for (k, v) in sorted(self.fields.items())
            ),
        )


class tuple_(WouldBeValue):
    def __init__(self, l=None):
        if l is None:
            l = []
        self.l = l
        self.line_no = get_file_line_no().export()

    def export(self):
        return "(%s tuple %s)" % (
            self.line_no,
            " ".join(spExpr(x).export() for x in self.l),
        )


def pair_(e1, e2):
    return tuple_([e1, e2])


class build_list(WouldBeValue):
    def __init__(self, l=None):
        if l is None:
            l = []
        self.l = l
        self.line_no = get_file_line_no().export()

    def push(self, other):
        return set_var(self, cons(spExpr(other), self))

    def map(self, f):
        return Expr("map_function", [self, spExpr(f)], get_file_line_no())

    def export(self):
        return "(%s list %s)" % (
            self.line_no,
            " ".join(spExpr(x).export() for x in self.l),
        )

    def concat(self):
        return Expr("concat", [self], get_file_line_no())

    def rev(self):
        return Expr("rev", [self], get_file_line_no())


class build_set(WouldBeValue):
    def __init__(self, l=None):
        if l is None:
            l = []
        self.l = l
        self.line_no = get_file_line_no().export()

    def contains(self, value):
        return Expr("contains", [self, spExpr(value)], get_file_line_no())

    def elements(self):
        return Expr("elements", [self], get_file_line_no())

    def rev_elements(self):
        return Expr("rev_elements", [self], get_file_line_no())

    def add(self, item):
        self.l.append(item)

    def remove(self, item):
        raise Exception("set.remove not implemented for scenario sets.")

    def export(self):
        return "(%s set %s)" % (
            self.line_no,
            " ".join(spExpr(x).export() for x in self.l),
        )


class mapOrBigMap(WouldBeValue):
    def __init__(self, l=None):
        if l is None:
            l = {}
        self.l = l
        self.line_no = get_file_line_no().export()

    def contains(self, value):
        return Expr("contains", [self, spExpr(value)], get_file_line_no())

    def __getitem__(self, item):
        return Expr("get_item", [self, spExpr(item)], get_file_line_no())

    def export(self):
        return "(%s %s %s)" % (
            self.line_no,
            self.name(),
            " ".join(
                "(%s %s)" % (spExpr(k).export(), spExpr(v).export())
                for (k, v) in self.l.items()
            ),
        )


class build_map(mapOrBigMap):
    def name(self):
        return "map"

    def items(self):
        return Expr("items", [self], get_file_line_no())

    def keys(self):
        return Expr("keys", [self], get_file_line_no())

    def values(self):
        return Expr("values", [self], get_file_line_no())

    def rev_items(self):
        return Expr("rev_items", [self], get_file_line_no())

    def rev_keys(self):
        return Expr("rev_keys", [self], get_file_line_no())

    def rev_values(self):
        return Expr("rev_values", [self], get_file_line_no())


class build_big_map(mapOrBigMap):
    def name(self):
        return "big_map"


def list_(l=None, t=None):
    l = build_list(l)
    return l if t is None else set_type_expr(l, TList(t))


def set_(l=None, t=None):
    l = build_set(l)
    return l if t is None else set_type_expr(l, TSet(t))


def map_or_big_map(big, l, tkey, tvalue):
    l = build_big_map(l) if big else build_map(l)
    if tkey is None and tvalue is None:
        return l
    else:
        t = TBigMap(tkey, tvalue) if big else TMap(tkey, tvalue)
        return set_type_expr(l, t)


def map_(l=None, tkey=None, tvalue=None):
    return map_or_big_map(False, l, tkey, tvalue)


def big_map_(l=None, tkey=None, tvalue=None):
    return map_or_big_map(True, l, tkey, tvalue)


def voting_power(address):
    return Expr("voting_power", [spExpr(address)], get_file_line_no())


def to_address(contract):
    return Expr("to_address", [spExpr(contract)], get_file_line_no())


def implicit_account(key_hash):
    return Expr("implicit_account", [spExpr(key_hash)], get_file_line_no())


def update_map(map, key, value):
    return Expr(
        "update_map", [spExpr(map), spExpr(key), spExpr(value)], get_file_line_no()
    )


def ediv(num, den):
    return Expr("ediv", [spExpr(num), spExpr(den)], get_file_line_no())


def pack(value):
    return Expr("pack", [spExpr(value)], get_file_line_no())


def unpack(value, t=None):
    return Expr("unpack", [spExpr(value), conv(t)], get_file_line_no())


def blake2b(value):
    return Expr("blake2b", [spExpr(value)], get_file_line_no())


def sha512(value):
    return Expr("sha512", [spExpr(value)], get_file_line_no())


def sha256(value):
    return Expr("sha256", [spExpr(value)], get_file_line_no())


def keccak(value):
    return Expr("keccak", [spExpr(value)], get_file_line_no())


def sha3(value):
    return Expr("sha3", [spExpr(value)], get_file_line_no())


def range(a, b, step=1):
    return Expr("range", [spExpr(a), spExpr(b), spExpr(step)], get_file_line_no())


def sum(value):
    return Expr("sum", [value], get_file_line_no())


def slice(expression, offset, length):
    return Expr(
        "slice",
        [spExpr(offset), spExpr(length), spExpr(expression)],
        get_file_line_no(),
    )


def constant(value, t=None):
    if not isinstance(value, str):
        raise Exception("%s should be a str literal" % str(value))
    return Expr("constant", [value, conv(t)], get_file_line_no())


def concat(value):
    return Expr("concat", [spExpr(value)], get_file_line_no())


def check_signature(pk, sig, msg):
    return Expr(
        "check_signature", [spExpr(pk), spExpr(sig), spExpr(msg)], get_file_line_no()
    )


def sign(e):
    return Expr("sign", [spExpr(e)], get_file_line_no())


def compare(x, y):
    return Expr("compare", [spExpr(x), spExpr(y)], get_file_line_no())


def spmax(x, y):
    return Expr("max", [spExpr(x), spExpr(y)], get_file_line_no())


def spmin(x, y):
    return Expr("min", [spExpr(x), spExpr(y)], get_file_line_no())


def split_tokens(amount, quantity, totalQuantity):
    return Expr(
        "split_tokens",
        [spExpr(amount), spExpr(quantity), spExpr(totalQuantity)],
        get_file_line_no(),
    )


def setInt(v):
    return Expr("int", [spExpr(v)], get_file_line_no())


def to_int(v):
    return Expr("to_int", [spExpr(v)], get_file_line_no())


def add(e1, e2):
    return Expr("add", [spExpr(e1), spExpr(e2)], get_file_line_no())


def mul(e1, e2):
    return Expr("mul", [spExpr(e1), spExpr(e2)], get_file_line_no())


def sub_mutez(e1, e2):
    return Expr("sub_mutez", [spExpr(e1), spExpr(e2)], get_file_line_no())


def is_nat(v):
    return Expr("is_nat", [spExpr(v)], get_file_line_no())


def as_nat(v, message=None):
    return is_nat(v).open_some(message=message)


# Timestamp helpers


def timestamp_from_utc(year, month, day, hours, minutes, seconds):
    return timestamp(
        pyInt(
            datetime.datetime(
                year, month, day, hours, minutes, seconds, tzinfo=datetime.timezone.utc
            ).timestamp()
        )
    )


def timestamp_from_utc_now():
    return timestamp(pyInt(datetime.datetime.now(datetime.timezone.utc).timestamp()))


def add_seconds(t, seconds):
    t = timestamp(t) if isinstance(t, pyInt) else t
    return Expr("add_seconds", [t, spExpr(seconds)], get_file_line_no())


def add_days(t, days):
    return add_seconds(t, days * (24 * 60 * 60))


def sapling_empty_state(memo_size):
    if not isinstance(memo_size, pyInt) or memo_size < 0 or memo_size > 65535:
        raise Exception(
            "sapling_empty_state(%s) expected a uint16 value as parameter (between 0 and 65535)"
            % memo_size
        )
    return Expr("sapling_empty_state", [memo_size], get_file_line_no())


def sapling_verify_update(state, transition):
    return Expr(
        "sapling_verify_update", [spExpr(state), spExpr(transition)], get_file_line_no()
    )


def ensure_str(name, x):
    if not isinstance(x, str):
        raise Exception("%s should be a str literal" % name)


def ensure_int(name, x):
    if not isinstance(x, pyInt):
        raise Exception("%s should be an int literal" % name)


def ensure_bytes(name, x):
    if not Helpers.areBytesValid(x):
        raise Exception("%s should be a bytes literal" % name)


def sapling_test_transaction(source, target, amount, memo_size, bound_data=None):
    if source is None:
        source = ""
    if target is None:
        target = ""
    ensure_str("test_sapling_transaction source", source)
    ensure_str("test_sapling_transaction target", target)
    ensure_int("test_sapling_transaction amount", amount)
    if amount < 0:
        raise Exception("test_sapling_transaction amount should be non-negative")
    if bound_data is None:
        raise Exception(
            "test_sapling_transaction without bound_data has been deprecated. See the Sapling integration page for a more comprehensive description of the Sapling protocol. https://octez.tezos.com/docs/active/sapling.html"
        )
    ensure_bytes("test_sapling_transaction bound_data", bound_data)
    return Expr(
        "literal",
        [
            Expr(
                "sapling_test_transaction",
                [memo_size, source, target, str(amount), bound_data],
            )
        ],
        get_file_line_no(),
    )


def contract_(t, address, entry_point="", entrypoint="", line_no=None):
    assert entry_point == "" or entrypoint == ""
    entrypoint = entrypoint or entry_point
    t = conv(t)
    line_no = get_file_line_no() if line_no is None else line_no
    return Expr("contract", [entrypoint, conv(t), spExpr(address)], line_no)


def view(name, address, param, t=None, line_no=None):
    t = conv(t)
    line_no = get_file_line_no() if line_no is None else line_no
    return Expr("view", [name, conv(t), spExpr(param), spExpr(address)], line_no)


def cast(expression, t):
    result = Expr("cast", [spExpr(expression), conv(t)], get_file_line_no())
    return result


def set_type_expr(expression, t):
    return cast(expression, t)


def fst(e):
    return Expr("first", [spExpr(e)], get_file_line_no())


def snd(e):
    return Expr("second", [spExpr(e)], get_file_line_no())


def len(e):
    return Expr("size", [spExpr(e)], get_file_line_no())


def poly_equal_expr(a, b):
    t = unknown()
    return pack(set_type_expr(a, t)) == pack(set_type_expr(b, t))


def is_failing(expression):
    return Expr("is_failing", [spExpr(expression)], get_file_line_no())


def catch_exception(expression, t=None):
    return Expr("catch_exception", [spExpr(expression), conv(t)], get_file_line_no())


def convert(expression):
    return Expr("convert", [spExpr(expression)], get_file_line_no())


def eif(c, a, b):
    return Expr("eif", [spExpr(c), spExpr(a), spExpr(b)], get_file_line_no())


def read_ticket(ticket):
    return Expr("read_ticket", [spExpr(ticket)], get_file_line_no())


def split_ticket(ticket, amounts):
    return Expr("split_ticket", [spExpr(ticket), spExpr(amounts)], get_file_line_no())


def join_tickets(ticket1, ticket2):
    return Expr("join_tickets", [spExpr((ticket1, ticket2))], get_file_line_no())


def test_ticket(ticketer, content, amount):
    line_no = get_file_line_no()
    return Expr(
        "test_ticket", [spExpr(ticketer), spExpr(content), spExpr(amount)], line_no
    )


class _List:
    def __getitem__(self, t):
        return TList(t)

    def __call__(self, l=None, t=None):
        return list_(l, t)


class _Map:
    def __getitem__(self, kv):
        k, v = kv
        return TMap(k, v)

    def __call__(self, l=None, t=None):
        return map_(l, t)


class _Set:
    def __getitem__(self, t):
        return TSet(t)

    def __call__(self, l=None, t=None):
        return set_(l, t)


class _BigMap:
    def __getitem__(self, kv):
        k, v = kv
        return TBigMap(k, v)

    def __call__(self, l=None, t=None):
        return big_map_(l, t)


class _Pair:
    def __getitem__(self, t12):
        t1, t2 = t12
        return TPair(t1, t2)

    def __call__(self, e1, e2):
        return pair_(e1, e2)


class _Tuple:
    def __getitem__(self, types):
        x = TTuple(*types)
        return x

    def __call__(self, l=None):
        return tuple_(l)


class _Option:
    def __getitem__(self, t):
        return TOption(t)


class _Contract:
    def __getitem__(self, t):
        return TContract(t)

    def __call__(self, t, address, entry_point="", entrypoint="", line_no=None):
        return contract_(t, address, entry_point, entrypoint, line_no)


class _Lambda_:
    def __call__(
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
        return TLambda(
            t1,
            t2,
            with_storage,
            with_operations,
            with_exceptions,
            with_mutez_overflow,
            with_mutez_underflow,
            tstorage,
        )


class _Bool(TType):
    def __call__(self, x):
        return literal("bool", x, pyBool)

    def export(self):
        return TSimple("bool").export()


class _IntOrNat(TType):
    def __call__(self, x):
        return literal("int_or_nat", x, pyInt)

    def export(self):
        return TSimple("int_or_nat").export()


class _Int(TType):
    def __call__(self, x):
        return literal("int", x, pyInt)

    def export(self):
        return TSimple("int").export()


class _Nat(TType):
    def __call__(self, x):
        return literal("nat", x, pyInt)

    def export(self):
        return TSimple("nat").export()


class _String(TType):
    def __call__(self, x):
        return literal("string", x, str)

    def export(self):
        return TSimple("string").export()


class _Bytes(TType):
    def __call__(self, x):
        if Helpers.areBytesValid(x):
            return literal("bytes", x, str)
        raise Exception(
            "sp.bytes('0x...') awaits a string in hexadecimal format and got '%s'. %s"
            % (str(x), pretty_line_no())
        )

    def export(self):
        return TSimple("bytes").export()


class _Mutez(TType):
    def __call__(self, x):
        if isinstance(x, pyInt):
            return literal("mutez", x, pyInt)
        else:
            raise ValueError(
                "sp.mutez(..) is for literals and awaits a python integers and got '%s' of type %s. %s\n\
Please use utils.nat_to_tez to convert a sp.nat expression into a sp.mutez expression."
                % (str(x), name_of_type(type(x)), pretty_line_no())
            )

    def export(self):
        return TSimple("mutez").export()


class _Timestamp(TType):
    def __call__(self, seconds):
        return literal("timestamp", seconds, pyInt)

    def export(self):
        return TSimple("timestamp").export()


class _Address(TType):
    def __call__(self, s):
        if s == "":
            raise Exception('"" is not a valid address')
        if not (
            any(s.startswith(prefix) for prefix in ["KT1", "tz1", "tz2", "tz3", "tz4"])
        ):
            raise Exception(
                '"%s" is not a valid address, it should start with tz1, tz2, tz3, tz4 or KT1.'
                % s
            )
        return literal("address", s, str)

    def export(self):
        return TSimple("address").export()


class _Key(TType):
    def __call__(self, s):
        return literal("key", s, str)

    def export(self):
        return TSimple("key").export()


class _Signature(TType):
    def __call__(self, sig):
        return literal("signature", sig, str)

    def export(self):
        return TSimple("signature").export()


class _RecordTypeOrValue:
    def __call__(self, **kargs):
        assert pyLen(kargs) > 0, "sp.record must have at least one field"
        if isinstance(pyList(kargs.values())[0], TType):
            return TRecord(**kargs)
        else:
            return record_(**kargs)


class _Variant:
    def __call__(self, *args, **kargs):
        if pyLen(args) == 2:
            const, x = pyList(args)
            return Expr("variant", [const, spExpr(x)], get_file_line_no())
        else:
            assert pyLen(args) == 0, "sp.variant: incorrect arguments"
            return TVariant(**kargs)

    def __getattr__(self, const):
        return lambda x: self.__call__(const, x)


def parse_account_or_address(account):
    if account is None:
        return "none"
    if isinstance(account, BaseTestAccount):
        return "seed:%s" % account.seed
    return spExpr(account).export()


# -- Contracts


class ContractId:
    def __init__(self, expr):
        self.expr = expr

    def __repr__(self):
        return str(self.expr)

    def export(self):
        return self.expr.export()


def static_contract_id(id):
    return ContractId(Expr("static_id", [id], get_file_line_no()))


def check_contract_id(context, contractId):
    if not isinstance(contractId, ContractId):
        raise Exception(
            f"sp.{context} applied to expression that is not a ContractId. {pretty_line_no()}"
        )


def contract_data(contractId):
    check_contract_id("contract_data", contractId)
    return Expr("contract_data", [contractId], get_file_line_no())


def contract_private(contractId):
    check_contract_id("contract_private", contractId)
    return Expr("contract_private", [contractId], get_file_line_no())


def contract_balance(contractId):
    check_contract_id("contract_balance", contractId)
    return Expr("contract_balance", [contractId], get_file_line_no())


def contract_address(contractId, entry_point="", entrypoint=""):
    assert entry_point == "" or entrypoint == ""
    entrypoint = entrypoint or entry_point
    check_contract_id("contract_address", contractId)
    return Expr("contract_address", [contractId, entrypoint], get_file_line_no())


def contract_baker(contractId):
    check_contract_id("contract_baker", contractId)
    return Expr("contract_baker", [contractId], get_file_line_no())


class ContractTyped:
    def __init__(self, contractId, entrypoint, line_no):
        self.contractId = contractId
        self.line_no = line_no
        self.entrypoint = entrypoint

    def export(self):
        return Expr(
            "contract_typed", [self.contractId, self.entrypoint], self.line_no
        ).export()

    def __getattr__(self, attr):
        if "__" in attr:
            raise AttributeError("")
        return Expr("contract_typed", [self.contractId, attr], self.line_no)


def contract_typed(contractId, entry_point="", entrypoint=""):
    assert entry_point == "" or entrypoint == ""
    entrypoint = entrypoint or entry_point
    check_contract_id("contract_typed", contractId)
    return ContractTyped(contractId, entrypoint, get_file_line_no())


class ParsedExpr(BaseParsedExpr):
    def __init__(self, sexpr):
        self.sexpr = sexpr

    def export(self):
        return self.sexpr


def expr(e):
    sexpr = parse_via_exe_or_js("<expr>", 0, 0, ParseKind.EXPR, e)
    return ParsedExpr(sexpr)


# -- Basic expressions or type constructors


list = _List()
map = _Map()
set = _Set()
big_map = _BigMap()
pair = _Pair()
tuple = _Tuple()
option = _Option()
contract = _Contract()
lambda_ = _Lambda_()
bool = _Bool()
int = _Int()
int_or_nat = _IntOrNat()
nat = _Nat()
string = _String()
bytes = _Bytes()
mutez = _Mutez()
timestamp = _Timestamp()
address = _Address()
key = _Key()
signature = _Signature()
record = _RecordTypeOrValue()
variant = _Variant()
unit = _Unit()
none = Expr("variant", ["None", unit_], LineNo("", -1))
