# Copyright 2025 - present Trilitech Limited, 2022-2024 Morum LLC


class Atom:
    def __init__(self, x):
        if type(x) != str:
            raise Exception("sexp.Atom: %s" % x)
        self.x = x

    def __str__(self):
        return self.x


class List:
    def __init__(self, *xs):
        xs = [Atom(x) if type(x) == str else x for x in xs]
        for x in xs:
            if type(x) not in [Atom, List]:
                raise Exception("sexp.of_List: %s" % x)
        self.xs = xs

    def __str__(self):
        return "(%s)" % " ".join(str(x) for x in self.xs)


def of_bool(x):
    if type(x) != bool:
        raise Exception("sexp.of_bool: %s" % x)
    return Atom(str(x))


def of_int(x):
    if type(x) != int:
        raise Exception("sexp.of_int: %s" % x)
    return Atom(str(x))


def of_str(x):
    if type(x) != str:
        raise Exception("sexp.of_str: %s" % x)
    return Atom(repr(x))


def of_option(f, x):
    return Atom("None") if x is None else List(Atom("Some"), f(x))
