import inspect
import os
import pathlib
import subprocess
import sys
from enum import Enum, unique

from ..internal.base import BaseTestAccount
from ..internal.module_elements import Instance, Method, View
from ..internal.modules import Module, load_module
from ..internal.utils import get_file_line_no, make_relative
from ..platform.runtime import (
    Runtime,
    get_disabled_server,
    get_make_file_dependencies,
    get_state,
)
from ..platform.services import interact
from ..public.syntax import (
    Expr,
    LineNo,
    contract_address,
    contract_baker,
    contract_balance,
    contract_data,
    contract_private,
    contract_typed,
    parse_account_or_address,
    poly_equal_expr,
    spExpr,
    static_contract_id,
)
from ..stdlib import load_library_if_needed
from ..stdlib.modules import STDLIB_MODULES


class Dynamic_contract:
    def __init__(self, scenario, id, views):
        self.contractId = static_contract_id(id)
        self.data = contract_data(self.contractId)
        self.balance = contract_balance(self.contractId)
        self.address = contract_address(self.contractId)
        self.baker = contract_baker(self.contractId)
        self.typed = contract_typed(self.contractId)
        self.scenario = scenario
        self.views = views

    # TODO __getattribute__, to hide "name", "args" etc.
    def __getattr__(self, attr):
        if attr in self.views:
            return View(self, attr)
        if attr == "address":
            return contract_address(self.contractId)
        if attr == "baker":
            return contract_baker(self.contractId)
        if attr == "balance":
            return contract_balance(self.contractId)
        if attr == "data":
            return contract_data(self.contractId)
        if attr == "private":
            return contract_private(self.contractId)
        if attr == "instantiation_result":
            return self.__dict__["instantiation_result"]
        return Method(self, attr)  # TODO limit to parser-obtained list of methods


# decorator for inline modules
def module(f):
    load_library_if_needed()
    if get_disabled_server():
        return None
    else:
        filename = make_relative(f.__code__.co_filename)
        line_no = LineNo(filename, f.__code__.co_firstlineno)
        code = inspect.getsource(f.__code__)
        return Module.make_inline_module(filename, line_no.line_no - 1, 0, code)


@unique
class SimulationMode(Enum):
    NATIVE = "native"
    MOCKUP = "mockup"
    GHOSTNET = "ghostnet"

    @classmethod
    def from_string(cls, s):
        return cls(s.lower())


class TestAccount(BaseTestAccount):
    def __init__(self, seed):
        self.seed = seed
        self.e = Expr("account_of_seed", [self.seed], get_file_line_no())
        self.address = self.e.address
        self.public_key_hash = self.e.public_key_hash
        self.public_key = self.e.public_key
        self.secret_key = self.e.secret_key

    def export(self):
        return self.e.export()


def test_account(seed):
    return TestAccount(seed)


class Scenario:
    # holds sets of deps for each module added with add_module
    _FILE_DEPENDENCIES = {}

    def __init__(self):
        self.messages = []
        self.exceptions = []
        self.failed = False
        self.entrypoint_calls = []
        self.modules = []

    def simulation_mode(self):
        data = {}
        data["action"] = "get_config"
        self.messages += [data]
        r = self.action(data)
        return SimulationMode.from_string(r["mode"][0])

    def add_module(self, m):
        load_library_if_needed()
        if not isinstance(m, Module):
            p = pathlib.Path(m)
            m = load_module(p, STDLIB_MODULES)
        assert m is not None
        if m in self.modules:
            return m
        data = {}
        data["action"] = "add_module"
        data["module_id"] = m.module_id.export()
        data["module"] = m.sexpr
        data["imports"] = m.export_imports()
        data["line_no"] = get_file_line_no().export()
        self.messages += [data]
        self.action(data)
        self._get_dependencies(m)
        self.modules.append(m)
        return m

    def _gen_dependencies(self, module):
        filenames = set()
        for m in module.ordered_imports():
            filename = m.module_id.filename
            if filename not in filenames:
                filenames.add(filename)
                yield filename, [
                    Module._make_filename(mm)[0] for mm in m.ordered_imports()
                ]
        filename = module.module_id.filename
        # last one shouldnt be in here - that would indicate a circular import - but check anyway
        if filename not in filenames:
            filenames.add(filename)
            yield filename, [
                Module._make_filename(mm)[0] for mm in module.ordered_imports()
            ]

    def _clean(self, nm):
        nms = pathlib.Path(nm).parts
        # note this is specific to our CI setup
        try:
            idx = nms.index("templates")
            subdirs = ["templates"] + list(nms[idx + 1 :])
            return str(pathlib.Path(*subdirs))
        except ValueError:
            pass
        # in our local setup want to convert
        # _build/test-venv/.../smartpy/STUFF
        # to
        # wheels/smartpy-tezos/smartpy/STUFF
        try:
            idx = nms.index("smartpy")
            subdirs = ["wheels", "smartpy-tezos", "smartpy"] + list(nms[idx + 1 :])
            return str(pathlib.Path(*subdirs))
        except ValueError:
            pass

        return nm

    def _get_dependencies(self, m):
        if get_make_file_dependencies() is None:
            return

        ky = self._clean(make_relative(m.module_id.filename))
        self._FILE_DEPENDENCIES[ky] = set()
        sections = list()
        for nm, deps in self._gen_dependencies(m):
            if not deps:
                continue
            nm = self._clean(make_relative(nm))
            if nm in self._FILE_DEPENDENCIES[ky]:
                continue
            self._FILE_DEPENDENCIES[ky].add(nm)
            deps = [self._clean(make_relative(d)) for d in deps]
            sections.append((nm, [d for d in deps]))
        try:
            # the scenario file that is calling this run
            # if multiple calls to add_module then last one overrides others
            nm = self._clean(make_relative(sys.argv[0]))
            sections.append(
                (nm, [ky for ky in self._FILE_DEPENDENCIES.keys() if ky != nm])
            )
        except IndexError as e:
            print(e, file=sys.stderr)

        try:
            # we need append mode as there maybe multiple calls to add_module
            # each make_file_dependencies is specific to a scenario
            # so append mode is ok here
            if sections and any(s for _, s in sections):
                with open(get_make_file_dependencies(), "a") as fh:
                    for nm, deps in sections:
                        if not deps:
                            continue
                        fh.write(f"\n{nm}:\n")
                        for d in deps:
                            fh.write(f"  {d}\n")
        except OSError as e:
            print(e, file=sys.stderr)

    def action(self, x):
        if not self.failed:
            return interact({"request": "scenario_action", "ix": self.ix, "action": x})

    def __iadd__(self, x):
        if isinstance(x, Instance):
            if x.scenario != self:
                raise Exception("The contract was instantiated in a different scenario")
            x.originate()
        else:
            raise Exception("Cannot add value of type %s to scenario" % str(type(x)))
        return self

    def dynamic_contract(self, template_ref, offset=None):
        data = {}
        data["action"] = "dynamic_contract"
        data["offset"] = str(offset) if offset is not None else "-1"
        data["line_no"] = get_file_line_no().export()
        data["module_id"] = template_ref.module.module_id.export()
        data["contract_name"] = template_ref.name
        self.messages += [data]
        id_ = self.action(data)

        # NOTE this returns all views, not just offchain ones
        data = {
            "action": "getOffchainViews",
            "id": static_contract_id(id_).export(),
            "line_no": get_file_line_no().export(),
        }
        self.messages += [data]
        xs = self.action(data)
        views = {x["name"] for x in xs}

        return Dynamic_contract(self, id_, views)

    def verify(self, condition):
        if isinstance(condition, bool):
            if not condition:
                raise Exception("Assert Failure")
        else:
            data = {}
            data["action"] = "verify"
            data["condition"] = spExpr(condition).export()
            data["line_no"] = get_file_line_no().export()
            self.messages += [data]
            self.action(data)

    def verify_equal(self, v1, v2):
        data = {}
        data["action"] = "verify"
        data["condition"] = poly_equal_expr(v1, v2).export()
        data["line_no"] = get_file_line_no().export()
        self.messages += [data]
        self.action(data)

    def compute(
        self,
        expression,
        sender=None,
        source=None,
        now=None,
        level=None,
        chain_id=None,
        voting_powers=None,
    ):
        data = {}
        data["action"] = "compute"
        data["expression"] = spExpr(expression).export()
        data["line_no"] = get_file_line_no().export()
        if chain_id is not None:
            data["chain_id"] = spExpr(chain_id).export()
        if level is not None:
            data["level"] = spExpr(level).export()
        if sender is not None:
            data["sender"] = parse_account_or_address(sender)
        if source is not None:
            data["source"] = parse_account_or_address(source)
        if now is not None:
            data["time"] = spExpr(now).export()
        if voting_powers is not None:
            data["voting_powers"] = spExpr(voting_powers).export()
        self.messages += [data]
        id = self.action(data)
        return Expr("var", [id], get_file_line_no())

    def show(self, expression, html=True, stripStrings=False, compile=False):
        data = {}
        data["action"] = "show"
        data["compile"] = compile
        data["expression"] = spExpr(expression).export()
        data["html"] = html
        data["line_no"] = get_file_line_no().export()
        self.messages += [data]
        self.action(data)

    def p(self, s):
        return self.tag("p", s)

    def h1(self, s):
        return self.tag("h1", s)

    def h2(self, s):
        return self.tag("h2", s)

    def h3(self, s):
        return self.tag("h3", s)

    def h4(self, s):
        return self.tag("h4", s)

    def tag(self, tag, s):
        data = {}
        data["action"] = "textBlock"
        data["inner"] = s
        data["line_no"] = get_file_line_no().export()
        data["tag"] = tag
        self.messages += [data]
        self.action(data)
        return self

    def add_flag(self, flag, *args):
        data = {}
        data["action"] = "flag"
        data["flag"] = [flag] + list(args)
        data["line_no"] = get_file_line_no().export()
        self.action(data)
        self.messages += [data]

    def prepare_constant_value(self, value, hash=None):
        data = {}
        data["action"] = "constant"
        data["kind"] = "value"
        data["hash"] = "None" if hash is None else hash
        data["expression"] = spExpr(value).export()
        data["line_no"] = get_file_line_no().export()
        self.messages += [data]
        id = self.action(data)
        return Expr("var", [id], get_file_line_no())

    def simulation(self, c):
        self.p("No interactive simulation available out of browser.")

    def test_account(self, seed, initial_balance=None, as_delegate=None):
        data = {}
        data["action"] = "register_account"
        data["seed"] = seed
        if initial_balance is not None:
            data["initial_balance"] = spExpr(initial_balance).export()
        if as_delegate is not None:
            data["as_delegate"] = bool(as_delegate)
        data["line_no"] = get_file_line_no().export()
        self.messages += [data]
        self.action(data)
        return test_account(seed)


def test_scenario(name, modules=None):
    load_library_if_needed()
    if modules is None:
        modules = []
    name = name.replace(" ", "_")
    scenario = Scenario()
    action = {"request": "new_scenario"}
    flags = []
    output_dir = os.environ.get("SMARTPY_OUTPUT_DIR")
    if name is not None:
        if output_dir is None:
            output_dir = name
        else:
            output_dir = str(pathlib.Path(output_dir, name))
    if get_state().runtime == Runtime.NATIVE and output_dir is not None:
        r = subprocess.run(["mkdir", "-p", output_dir])
        assert r.returncode == 0
        flags += ["--output", output_dir]
    more_flags = os.environ.get("SMARTPY_FLAGS")
    if more_flags is not None:
        flags += more_flags.split()
    action["flags"] = flags
    r = interact(action)
    scenario.ix = r

    if type(modules) != list:
        modules = [modules]
    for module in modules:
        scenario.add_module(module)
    get_state().current_scenario = scenario
    return scenario


def add_test(name=None):
    if name:
        raise Exception(
            "sp.add_test no longer takes the name argument. Please provide it to sp.test_scenario instead."
        )

    def r(f):
        if not get_disabled_server():
            get_state().current_scenario = None
            f()
            get_state().current_scenario = None

    return r
