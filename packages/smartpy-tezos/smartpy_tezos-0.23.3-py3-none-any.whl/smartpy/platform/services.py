import base64
import json
import subprocess
import sys
from enum import Enum, auto, unique

from ..internal.state import get_state
from ..internal.utils import get_wheel_file
from ..public.exceptions import FailwithException, RuntimeException, TypeError_
from .runtime import Runtime, get_debug

_DN2 = [
    "ok_int",
    "ok_config",
    "ok_instantiation_result",
    "ok_originate_contract",
    "ok_show_value",
    "ok_message",
    "ok_offchain_views",
    "ok_scenario_var_id",
]


@unique
class ParseKind(Enum):
    SMARTPY = auto()
    SMARTPY_STDLIB = auto()
    MODULE = auto()
    EXPR = auto()

    def to_string(self):
        if self is ParseKind.SMARTPY:
            return "load"
        elif self is ParseKind.SMARTPY_STDLIB:
            return "load"
        elif self is ParseKind.MODULE:
            return "module"
        elif self is ParseKind.EXPR:
            return "expr"


class ParseError(Exception):
    pass


def parser_via_exe(filename, row_offset, col_offset, kind, code):
    proc = subprocess.Popen(
        get_state().canopy
        + [
            "parse",
            filename,
            str(row_offset),
            str(col_offset),
            kind,
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        encoding="utf-8",
    )
    r, _stderr = proc.communicate(code)
    if proc.returncode:
        raise Exception(f"parser interaction error: exit status {proc.returncode}")
    return json.loads(r)


def parser_via_js(filename, row_offset, col_offset, kind, code):
    import js
    import pyodide

    # NOTE https://pyodide.org/en/0.22.1/usage/api/python-api/ffi.html#pyodide.ffi.JsProxy
    x1 = pyodide.ffi.to_js((filename, row_offset, col_offset))
    x2 = pyodide.ffi.to_js((kind, code))
    y = js.parse(x1, x2)
    return y.to_py()


def parse_via_exe_or_js(filename, row_offset, col_offset, kind, code):
    if sys.platform == "emscripten":
        (status, result) = parser_via_js(
            filename, row_offset, col_offset, kind.to_string(), code
        )
    else:
        (status, result) = parser_via_exe(
            filename, row_offset, col_offset, kind.to_string(), code
        )
    if status == "ok":
        return result
    elif status == "error":
        print(result, file=sys.stderr)
        raise ParseError(result)
    else:
        raise Exception(f"parser interaction error: {status} {result}")


def display_action_result(action, output):
    """
    Display the result of an action in a Jupyter notebook.
    """
    try:
        from IPython.display import HTML, display

        # Load and display the jupyter-web-components.js content directly
        _js_content = get_wheel_file("jupyter-web-components.js")

        r = base64.b64encode(
            f'[["{action}", {json.dumps(output)}]]'.encode("utf-8")
        ).decode("utf-8")
        o = f"""<jupyter-output dark="false" compilation_state="compiled" output="{r}"></jupyter-output>"""
        # Display isn't doing anything if there is no output,
        # for example in a Python environment with IPython installed without a notebook.
        display(HTML(o))
    except (ImportError, FileNotFoundError):
        pass


def interact(up):
    debug = get_debug()
    if debug:
        print("[smartpy] up %s" % up, file=sys.stderr)
    up = json.dumps(up)
    runtime = get_state().runtime
    if runtime == Runtime.IDE or runtime == Runtime.JUPYTER_LITE:
        import js

        dn = js.smartpy.step(up)
    else:
        oasis = get_state().oasis
        oasis.stdin.write(up)
        oasis.stdin.write("\n")
        oasis.stdin.flush()
        dn = oasis.stdout.readline().rstrip("\n")
    if debug:
        print("[smartpy] dn %s" % dn, file=sys.stderr)
    dn = json.loads(dn)
    if dn[0] == "ok_unit":
        assert len(dn) == 1
        return
    elif dn[0] in _DN2:
        assert len(dn) == 2
        if dn[0] == "ok_originate_contract":
            display_action_result("Originate_contract", dn[1])
        elif dn[0] == "ok_message":
            display_action_result("Message_node", dn[1])
        elif dn[0] == "ok_show_value":
            display_action_result("Show_value", dn[1])
        return dn[1]
    elif dn[0] == "error":
        assert len(dn) == 2
        if dn[1][0] == "SmartPy_error":
            error = dn[1][1]
            if error["type_"][0] == "Type_error":
                raise TypeError_(**error["context"])
            elif error["type_"][0] == "Runtime_error":
                raise RuntimeException(**error["context"])
            elif error["type_"][0] == "Reached_failwith":
                raise FailwithException(**error["context"], **error["type_"][1])
            else:
                raise Exception("Unknown SmartPy error, please report: " + str(dn))
        elif dn[1][0] == "Failure":
            raise Exception("Internal SmartPy error, please report: " + dn[1][1])
        else:
            raise Exception("Unknown SmartPy error, please report: " + str(dn))
    else:
        raise Exception("Unknown response tag '%s'" % dn[0])


def showTraceback(title, trace):
    def formatErrorLine(line):
        i = -1
        while i + 2 < len(line) and line[i + 1] == " ":
            i += 1
        if 0 <= i:
            line = i * "&nbsp;" + line[i + 1 :]
        return line

    title = "Error: " + str(title)
    lines = []
    skip = False
    print(trace)
    for line in trace.split("\n"):
        if not line:
            continue
        if skip:
            skip = False
            continue
        skip = "module smartpy line" in line or (
            "module __main__" in line and "in run" in line
        )
        if "Traceback (most recent call last):" in line:
            line = ""
        if not skip:
            lineStrip = line.strip()
            lineId = None
            line = formatErrorLine(line)
            if lineStrip.startswith("module <module>") or lineStrip.startswith(
                "File <string>"
            ):
                lineId = line.strip().split()[3].strip(",")
            line = line.replace("module <module>", "SmartPy code").replace(
                "File <string>", "SmartPy code"
            )
            if "SmartPy code" in line:
                line = "<span class='partialType'>%s</span>" % (line)
            if lineId:
                line = (
                    line
                    + " <button class=\"text-button\" onClick='showLine(%s)'>(line %s)</button>"
                    % (lineId, lineId)
                )
            lines.append(line)
    error = title + "\n\n" + lines[0] + "\n\n" + "\n".join(lines[1:-1])

    import js

    js.window.smartpyContext.showError(
        "<div class='michelson'>%s</div>" % (error.replace("\n", "\n<br>"))
    )
