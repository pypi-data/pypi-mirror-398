from ..public.metadata import InstanceOffchainViewsMetadata
from ..public.syntax import (
    Expr,
    contract_address,
    contract_baker,
    contract_balance,
    contract_data,
    contract_private,
    parse_account_or_address,
    record_,
    spExpr,
    static_contract_id,
    unit_,
)
from . import sexp
from .base import BaseRef, BaseTypeRef
from .state import get_state
from .utils import get_file_line_no, pretty_line_no


# m.C
class ContractClass:
    def __init__(self, module, name, views):
        self.module = module
        self.name = name
        self.views = views

    def __call__(self, *args, **kargs):
        if args and kargs:
            raise AttributeError("Cannot mix positional and keyword arguments.")
        return Instance(self, args, kargs)


# m.C()
class Instance:
    def __init__(self, contract_class, args, kargs):
        assert (
            get_state().current_scenario is not None
        ), "Contract instantiation must occur after the call of sp.test_scenario."
        self.contract_class = contract_class
        self.scenario = get_state().current_scenario

        get_state().current_scenario.add_module(self.contract_class.module)
        self.args = [spExpr(x) for x in args]
        self.kargs = [(k, spExpr(v)) for k, v in kargs.items()]
        data = {}
        data["action"] = "instantiateContract"
        data["module_id"] = self.contract_class.module.module_id.export()
        data["name"] = self.contract_class.name
        data["args"] = "(" + " ".join(x.export() for x in self.args) + ")"
        data["kargs"] = (
            "("
            + " ".join(("(" + k + " " + v.export() + ")") for k, v in self.kargs)
            + ")"
        )
        data["line_no"] = get_file_line_no().export()
        self.instantiation_result = self.scenario.action(data)
        self.contractId = static_contract_id(
            self.instantiation_result["id"]["static_id"]
        )

    def originate(self):
        self.origination_result = self.scenario.action(
            {
                "action": "originateContract",
                "id": self.contractId.export(),
                "line_no": get_file_line_no().export(),
            }
        )

    def get_offchain_views(self):
        return InstanceOffchainViewsMetadata(
            self.scenario.action(
                {
                    "action": "getOffchainViews",
                    "id": self.contractId.export(),
                    "line_no": get_file_line_no().export(),
                }
            )
        )

    def get_source(self):
        return self.instantiation_result["input"]

    def get_generated_michelson(self):
        return self.instantiation_result["generated_michelson"]

    def get_error_map(self):
        return self.instantiation_result["error_map"]

    def set_initial_balance(self, balance):
        if isinstance(balance, int):
            raise Exception(
                "balance should be in tez or mutez and not int (use sp.tez(..) or sp.mutez(..)). %s"
                % (pretty_line_no())
            )
        return self.scenario.action(
            {
                "action": "setContractBalance",
                "id": self.contractId.export(),
                "balance": spExpr(balance).export(),
                "line_no": get_file_line_no().export(),
            }
        )

    # TODO __getattribute__, to hide "name", "args" etc.
    def __getattr__(self, attr):
        if attr in self.contract_class.views:
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


# m.C().f
class View:
    def __init__(self, instance, name):
        self.instance = instance
        self.name = name

    def __call__(self, args=unit_):
        return Expr(
            "static_view",
            [self.instance.contractId, self.name, spExpr(args)],
            get_file_line_no(),
        )


# m.C().f
class Method:
    def __init__(self, instance, name):
        self.instance = instance
        self.name = name

    def __call__(self, *args, **kargs):
        sc = self.instance.scenario
        record_fields = {}
        special_args = {}
        for k, v in kargs.items():
            if k[:2] == "__":
                record_fields[k[1:]] = v
            elif k[0] == "_":
                special_args[k] = v
            else:
                record_fields[k] = v
        if sc is None:
            raise Exception(
                "Must add contract to scenario before calling its entrypoints."
            )
        if args and record_fields:
            raise Exception(
                "Entrypoints can be called with either arguments or keyword arguments, not both."
            )
        if args:
            params = spExpr(args[0])
        elif record_fields:
            params = record_(**{k: spExpr(v) for (k, v) in record_fields.items()})
        else:
            params = ()
        action = {
            "action": "message",
            "id": self.instance.contractId.export(),
            "line_no": get_file_line_no().export(),
            "message": self.name,
            "params": spExpr(params).export(),
        }
        for k, v in special_args.items():
            k = k[1:]
            if k in [
                "exception",
                "voting_powers",
                "amount",
                "chain_id",
                "level",
            ]:
                action[k] = spExpr(v).export()
            elif k in ["source", "sender"]:
                action[k] = parse_account_or_address(v)
            elif k == "now":
                action["time"] = spExpr(v).export()
            elif k == "valid":
                action[k] = v
            else:
                raise Exception("Unknown argument: _%s" % k)
        sc.entrypoint_calls.append((self.instance, sc.action(action)))


# m.t
class TypeRef(BaseTypeRef):
    def __init__(self, module, name):
        self.module = module
        self.name = name
        self.line_no = get_file_line_no()

    def export(self):
        line_no = self.line_no.export()
        return str(sexp.List("typeRef", self.module.name, self.name, line_no))


# m.x
class Ref(BaseRef):
    def __init__(self, module, name):
        self.module = module
        self.name = name
        self.line_no = get_file_line_no()
        if get_state().current_scenario:
            get_state().current_scenario.add_module(self.module)

    def export(self):
        line_no = self.line_no.export()
        module = sexp.List(line_no, "var", self.module.name)
        return str(sexp.List(line_no, "attr", module, self.name))

    def __call__(self, arg):
        line_no = self.line_no.export()
        module = sexp.List(line_no, "var", self.module.name)
        f = sexp.List(line_no, "attr", module, self.name)
        return Expr("call", [f, spExpr(arg)], get_file_line_no())

    def apply(self, arg):
        line_no = self.line_no.export()
        module = sexp.List(line_no, "var", self.module.name)
        f = sexp.List(line_no, "attr", module, self.name)
        return Expr("apply", [f, spExpr(arg)], get_file_line_no())
