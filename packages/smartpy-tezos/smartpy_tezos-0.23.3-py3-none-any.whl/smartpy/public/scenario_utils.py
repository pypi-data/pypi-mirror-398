from .syntax import big_map, bytes, map, set_type_expr
from .types import TIntOrNat, TMap


def vector_raw(xs):
    return map(l={k: v for (k, v) in enumerate(xs)})


def matrix_raw(xs):
    return vector_raw([vector_raw(x) for x in xs])


def cube_raw(xs):
    return vector_raw([matrix_raw(x) for x in xs])


def vector(xs, tkey=TIntOrNat, tvalue=None):
    return set_type_expr(vector_raw(xs), TMap(tkey, tvalue))


def matrix(xs, tkey=TIntOrNat, tvalue=None):
    return set_type_expr(matrix_raw(xs), TMap(tkey, TMap(tkey, tvalue)))


def cube(xs, tkey=TIntOrNat, tvalue=None):
    return set_type_expr(cube_raw(xs), TMap(tkey, TMap(tkey, TMap(tkey, tvalue))))


def bytes_of_string(s):
    if not (isinstance(s, str)):
        raise Exception(
            "sp.bytes_of_string must be applied to constant strings and got (%s)"
            % (str(s))
        )
    return bytes("0x" + s.encode("utf-8").hex())


def metadata_of_url(url):
    return big_map({"": bytes_of_string(url)})
