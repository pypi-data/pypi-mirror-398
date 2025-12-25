import typing

from ..internal.modules import Module, ParseKind
from ..internal.utils import LineNo, get_file_line_no
from ..platform.services import parse_via_exe_or_js
from ..public.metadata import (
    CodeMismatchException,
    are_equivalent_micheline,
    check_sp_version,
    normalize_micheline,
)
from ..public.scenario import test_scenario


def load_module_from_metadata(module):
    filename, line = module["line_no"][0], module["line_no"][1]
    line_no = LineNo(filename, line)
    code = module["source"]
    kind = module["module_kind"]
    name = module["name"]
    if kind == "inline_python":
        return Module.make_inline_module(filename, line - 3, 0, code)
    elif kind == "smartpy":
        return Module.make_smartpy_module(filename, code)
    elif kind == "smartpy_stdlib":
        return Module.make_smartpy_stdlib_module(filename, code, name)
    else:
        raise ValueError(f"Unknown module ID kind: {kind} for {name}")


def instantiate_from_metadata(
    metadata: typing.Dict[str, typing.Any], code_metadata: typing.Dict[str, typing.Any]
):
    check_sp_version(metadata)
    offset = 0
    file = get_file_line_no().filename
    args = [
        parse_via_exe_or_js(file, offset, 0, ParseKind.EXPR, p)
        for p in code_metadata["param"]
    ]
    sc = test_scenario("Check validity")
    sc.h2("Check validity")
    # Add flags
    for flag in code_metadata["flags"]:
        sc.add_flag(*flag)
    # Add modules - imports first
    for module in code_metadata["imports"]:
        m = load_module_from_metadata(module)
        sc.add_module(m)
    # Add modules - then main one
    main_module = load_module_from_metadata(code_metadata["module_"])
    sc.add_module(main_module)
    # Instantiate the contract
    c1 = main_module.__getattr__(code_metadata["name"])(*args)
    # Originate the contract
    sc += c1
    return c1.get_generated_michelson()


def check_validity(
    metadata: typing.Dict[str, typing.Any],
    code_metadata: typing.Dict[str, typing.Any],
    onchain_michelson: typing.List[typing.Any],
):
    """Checks that the code given in the metadata generates the same onchain code.

    Args:
        metadata (dict): Metadata dictionary.
            Can be obtained from `sp.get_metadata()`.
        code_metadata (dict): Code metadata dictionary.
            Can be obtained from `sp.get_metadata_code()`.
        onchain_michelson (List[any]): On-chain Michelson representation in the micheline (JSON) format.
            Can be obtained from `sp.get_michelson_code()`.

    Returns:
        A tuple containing the generated michelson and details of the first difference
        if a mismatch is found (diff path, generated value, onchain value), or None if
        the generated code matches the on-chain code.

    Raises:
        CodeMismatchException: If the generated code from metadata does not match the on-chain code.
                               The exception contains the generated michelson and details of the first difference.

    Example:
        >>> import smartpy as sp
        ...
        ... address = "KT1EQLe6AbouoX9RhFYHKeYQUAGAdGyFJXoi"
        ... metadata = sp.get_metadata(address, network="ghostnet")
        ... code_metadata = sp.get_metadata_code(metadata)
        ... onchain_michelson = sp.get_michelson_code(address, network="ghostnet")
        ... try:
        ...     sp.check_validity(metadata, code_metadata, onchain_michelson)
        ...     print("Metadata code is valid")
        ... except CodeMismatchException as e:
        ...     print(e)
        ...     print("Generated michelson:", e.generated_michelson)
        ...     print("Details of the first difference:", e.diff_details)
    """

    def get_value_at_path(micheline, diff_path):
        for p in diff_path:
            micheline = micheline[p]
        return micheline

    generated_michelson = normalize_micheline(
        instantiate_from_metadata(metadata, code_metadata)
    )
    onchain_michelson = normalize_micheline(onchain_michelson)
    is_equal, first_diff = are_equivalent_micheline(
        generated_michelson, onchain_michelson
    )
    if not is_equal:
        raise CodeMismatchException(
            generated_michelson,
            (
                first_diff,
                get_value_at_path(generated_michelson, first_diff),
                get_value_at_path(onchain_michelson, first_diff),
                get_value_at_path(generated_michelson, first_diff),
            ),
        )
