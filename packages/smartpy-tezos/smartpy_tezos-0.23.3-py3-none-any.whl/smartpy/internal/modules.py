import os
import pathlib
from collections import OrderedDict
from site import addsitepackages, getsitepackages, getusersitepackages

from ..platform.runtime import get_disabled_server
from ..platform.services import ParseKind, parse_via_exe_or_js
from . import sexp
from .module_elements import ContractClass, Ref, TypeRef
from .utils import expand_resolve, get_file_line_no, make_relative


def _get_smartpy_includes():
    # follow python module import idea - https://docs.python.org/3/tutorial/modules.html#the-module-search-path
    # so search current dir first, then PYTHONPATH,
    # then look into a built-in default dir
    pythonpath = os.environ.get("PYTHONPATH")
    pypaths = []
    if pythonpath is not None:
        pypaths = [expand_resolve(pth) for pth in pythonpath.split(":")]
    smartpy_includes = [
        pth for pth in pypaths + [getusersitepackages()] + getsitepackages() if pth
    ]
    return list(addsitepackages(set(smartpy_includes)))


def read_smartpy_code(fn):
    filenames = [make_relative(fn)] + [
        os.path.join(ff, fn) for ff in _get_smartpy_includes()
    ]
    for filename in filenames:
        try:
            with open(filename, "r") as f:
                code = f.read()
            return make_relative(filename), code
        except FileNotFoundError:
            # ignore until we have tried everything
            continue

    # tried everything so error
    raise FileNotFoundError(fn)


class ModuleId:
    def __init__(self, filename, kind, name):
        self.filename = str(make_relative(os.path.normpath(filename)))
        self.kind = kind
        self.name = name

    @staticmethod
    def _helper(module_id_kind_str, path, name):
        return str(sexp.List("module_id", module_id_kind_str, path, name))

    def export(self):
        if self.kind is ParseKind.MODULE:
            return self._helper("inline_python", self.filename, self.name)
        elif self.kind is ParseKind.SMARTPY:
            return self._helper("smartpy", self.filename, self.name)
        elif self.kind is ParseKind.SMARTPY_STDLIB:
            return self._helper("smartpy_stdlib", self.filename, self.name)
        else:
            raise ValueError(f"Unknown module_id kind: {self.kind}")


class Module:
    SMARTPY_EXTENSION = ".spy"

    _INLINE_MODULES = {}

    def __init__(self, module_id, sexpr, elements, imports, imported_path):
        self.module_id = module_id
        self.sexpr = sexpr
        self.elements = {}
        for k, v in elements:
            self.elements[k] = v
        self.imports = imports  # can be [dict] or [Module]
        self.imported_path = imported_path

    @property
    def name(self):
        return self.module_id.name

    # TODO instead of __getattr__ initialize things via self.x?
    # or use __getattribute__ instead?
    def __getattr__(self, attr):
        if attr in self.elements:
            kind, info = self.elements[attr]
            if kind == "typeDef":
                return TypeRef(self, attr)
            elif kind == "def":
                return Ref(self, attr)
            elif kind == "contractClass":
                return ContractClass(self, attr, info)
            else:
                assert False
        else:
            raise AttributeError("No such attribute: %s" % (attr))

    @classmethod
    def _parse(cls, filename, rowOffset, colOffset, kind, code, imported_path):
        moduleName, sexpr, els, imports = parse_via_exe_or_js(
            filename, rowOffset, colOffset, kind, code
        )
        module_id = ModuleId(filename, kind, moduleName)
        return cls(module_id, sexpr, els, imports, imported_path)

    @staticmethod
    def _check_inline_module_cache(im):
        # im can be a module or a dict {name, path},
        # when it is a dict,
        # if it is imported as `import X` then name is X and path = []
        # if it is imported as `import X as Y` then name is Y (ignored) and path is [X]
        if isinstance(im, Module):
            return Module._INLINE_MODULES.get(im.name)

        try:
            return Module._INLINE_MODULES[
                im["name"]
            ]  # import X            <- key would be X
        except KeyError:
            try:
                return Module._INLINE_MODULES[
                    im["path"][0]
                ]  # import X as Y    <- key would be X
            except:
                return None

    @staticmethod
    def _parse_with_cycle_detection(
        filename,
        rowOffset,
        colOffset,
        kind,
        code,
        modules=None,
        visited=None,
        cycles=None,
        imported_path=None,
        inlineModule=None,
    ):
        # keep a list of modules to return to caller
        if modules is None:
            modules = []
        # keep a set of imports we have already done
        if visited is None:
            visited = {}
        # for checking import cycles, ordered for a decent error msg
        if cycles is None:
            cycles = OrderedDict()
        # the dotted path of the import - turned into filename
        if imported_path is None:
            imported_path = []

        m = (
            inlineModule
            if inlineModule is not None
            else Module._parse(
                filename, rowOffset, colOffset, kind, code, imported_path
            )
        )
        visited[filename] = m
        cycles[filename] = m

        for im in m.imports:
            mm = Module._check_inline_module_cache(im)
            if mm is not None:
                newFilename = f"{mm.module_id.filename}#{mm.name}"

                if newFilename in cycles:
                    ks = list(cycles.keys())
                    ks.append(newFilename)
                    cycle = " ->\n".join(str(make_relative(k)) for k in ks)
                    raise Exception(f"import cycle detected:\n{cycle}")

                if newFilename in visited:
                    continue

                visited_inline_subset, _ = Module._parse_with_cycle_detection(
                    newFilename,
                    0,
                    0,
                    ParseKind.MODULE,
                    "not needed",
                    modules,
                    visited,
                    cycles,
                    imported_path,
                    inlineModule=mm,
                )
                visited.update(visited_inline_subset)
            else:
                newFilename, imported_path = Module._make_filename(im)
                newFilename, newCode = read_smartpy_code(newFilename)

                if newFilename in cycles:
                    ks = list(cycles.keys())
                    ks.append(newFilename)
                    cycle = " ->\n".join(str(make_relative(k)) for k in ks)
                    raise Exception(f"import cycle detected:\n{cycle}")

                if newFilename in visited:
                    continue

                # NOTE these are smartpy imports - will be of kind=load, from (0, 0)
                visited_subset, _ = Module._parse_with_cycle_detection(
                    newFilename,
                    0,
                    0,
                    ParseKind.SMARTPY,
                    newCode,
                    modules,
                    visited,
                    cycles,
                    imported_path,
                )
                visited.update(visited_subset)

        del cycles[filename]
        # add this module after recursing into dependents
        modules.append(m)
        return visited, modules[::-1]

    @staticmethod
    def _make_filename(im):
        if isinstance(im, Module):
            return im.module_id.filename, im.imported_path

        else:
            imPath = im["path"]
            imStub = os.path.join(*imPath)
            return f"{imStub}{Module.SMARTPY_EXTENSION}", imPath

    def ordered_imports(self):
        return self.imports[::-1]

    def export_imports(self):
        # NOTE reverse the imports list to do dependents first
        line_no = get_file_line_no()
        return str(
            sexp.List(
                *[
                    sexp.List(
                        line_no.export(),
                        "imported_module",
                        m.module_id.export(),
                        sexp.List(*m.imported_path),
                        m.sexpr,
                    )
                    for m in self.ordered_imports()
                ]
            )
        )

    @classmethod
    def make_inline_module(cls, filename, rowOffset, colOffset, code):
        """
        parses the local module source code and recurses into all imports.

        returns:
            a module in a form suitable for export to oasis
        """
        _, xs = cls._parse_with_cycle_detection(
            filename, rowOffset, colOffset, ParseKind.MODULE, code
        )
        assert len(xs) > 0, f"Failed to load file: {filename}"
        m, *importedModules = xs
        ret = Module(
            m.module_id, m.sexpr, m.elements.items(), importedModules, m.imported_path
        )
        cls._INLINE_MODULES[m.name] = ret
        return ret

    @classmethod
    def make_smartpy_module(cls, filename, code):
        """
        parses the module source code and recurses into all imports.

        returns:
            a module in a form suitable for export to oasis
        """
        _, xs = cls._parse_with_cycle_detection(
            filename,
            0,
            0,
            ParseKind.SMARTPY,
            code,
        )
        assert len(xs) > 0, f"Failed to load file: {filename}"
        m, *importedModules = xs
        return Module(
            m.module_id, m.sexpr, m.elements.items(), importedModules, m.imported_path
        )

    @classmethod
    def make_smartpy_stdlib_module(cls, filename, code, name):
        """
        parses the module source code and recurses into all imports.

        returns:
            a module in a form suitable for export to oasis
        """
        _, xs = cls._parse_with_cycle_detection(
            filename, 0, 0, ParseKind.SMARTPY_STDLIB, code
        )
        assert len(xs) > 0, f"Failed to load file: {filename}"
        m, *importedModules = xs
        # NOTE we use the given `name` here
        module_id = ModuleId(filename, ParseKind.SMARTPY_STDLIB, name)
        return Module(
            module_id, m.sexpr, m.elements.items(), importedModules, m.imported_path
        )


def load_module(fn, stdlib_modules=None):
    if stdlib_modules is None:
        stdlib_modules = []
    if get_disabled_server():
        return None
    else:
        # Backward compatibility for old stdlib
        fn_path = fn if isinstance(fn, pathlib.Path) else pathlib.Path(fn)
        if fn_path.is_relative_to(pathlib.Path("smartpy/lib/")):
            fn = pathlib.Path("smartpy/stdlib/") / fn_path.relative_to(
                pathlib.Path("smartpy/lib/")
            )
        filename, code = read_smartpy_code(fn)
        if str(fn).startswith("smartpy/stdlib/") and str(fn).endswith(".spy"):
            name = str(fn)[len("smartpy/stdlib/") : -len(".spy")]
            if name in stdlib_modules:
                return Module.make_smartpy_stdlib_module(filename, code, name)
        return Module.make_smartpy_module(filename, code)
