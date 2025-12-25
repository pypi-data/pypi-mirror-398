import os
import platform
import subprocess
import sys
from enum import Enum, auto, unique
from os.path import dirname, join

from .. import config
from ..internal.state import get_state
from ..internal.utils import get_wheel_file


@unique
class Runtime(Enum):
    JUPYTER_LITE = auto()  # JavaScript/Pyodide in Jupyter Lite
    IDE = auto()  # JavaScript/Pyodide in SmartPy web IDE
    NATIVE = auto()  # Native Python


def _init_jupyter_lite():
    """
    Initialize Jupyter Lite environment by loading SmartPy JavaScript modules.

    Sets up the browser-based SmartPy backend (Oasis/Canopy) and configures
    the JavaScript bridge for communication between Python and the backend.
    """
    if get_state().runtime != Runtime.JUPYTER_LITE:
        raise Exception(
            "Cannot initialize Jupyter Lite environment in non-Jupyter runtime"
        )

    import js
    import pyodide
    from IPython.display import Javascript, display

    # js.eval() is executed within the service worker
    # Javascript() is executed within the main thread

    oasisLibsCode = get_wheel_file("browserOasisLibs.js")
    oasisCode = get_wheel_file("browserOasis.js")
    canopyCode = get_wheel_file("browserCanopy.js")

    # Executed in the service worker

    js.module = pyodide.ffi.to_js({})
    js.eval(oasisLibsCode)

    js.module = pyodide.ffi.to_js({})
    js.eval(oasisCode)
    js.smartpy = js.Oasis.smartpy
    js.parse = js.smartpy.step

    js.module = pyodide.ffi.to_js({})
    js.eval(canopyCode)

    js.eval("globalThis.smartpyContext.addOutput = (x) => console.log(x)")

    # Executed in the main thread

    # Jupyter Web Components
    js_content = get_wheel_file("jupyter-web-components.js")
    display(Javascript(js_content))
    # Google Analytics
    display(
        Javascript(
            """if (window.trackGoogleAnalyticsEvent) {
                window.trackGoogleAnalyticsEvent({
                category: 'smartpy code execution',
                action: 'import smartpy',
                label: 'execute the import smartpy in Jupyter Lite',
                });
            }"""
        )
    )


def _get_command(name):
    use_docker = os.environ.get("SMARTPY_USE_DOCKER") is not None
    _system = platform.system()
    _machine = platform.machine()
    c = os.environ.get("SMARTPY_" + name.upper())
    if c:
        return c.split()
    else:
        if use_docker or (_system, _machine) == ("Darwin", "x86_64"):
            return [
                join(dirname(dirname(__file__)), "smartpy-docker"),
                config.docker_image,
                name,
            ]
        elif (_system, _machine) == ("Linux", "x86_64"):
            return [join(dirname(dirname(__file__)), "smartpy-" + name + "-linux.exe")]
        elif (_system, _machine) == ("Darwin", "arm64"):
            return [join(dirname(dirname(__file__)), "smartpy-" + name + "-macOS.exe")]
        else:
            raise Exception(f"Platform {_system}-{_machine} not supported.")


def _init_oasis():
    state = get_state()
    if state.runtime != Runtime.NATIVE:
        raise Exception("Cannot initialize Oasis backend in non-native Python")
    if not get_disabled_server():
        state.oasis = subprocess.Popen(
            _get_command("oasis"),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            encoding="utf-8",
        )
    else:
        state.oasis = _get_command("oasis")


def _init_canopy():
    state = get_state()
    if state.runtime != Runtime.NATIVE:
        raise Exception("Cannot initialize Canopy backend in non-native Python")
    state.canopy = _get_command("canopy")


def _init_ide():
    if get_state().runtime != Runtime.IDE:
        raise Exception("Cannot initialize IDE backend in non-IDE runtime")
    import importlib

    import js

    from .services import showTraceback

    def evalRun(withTests):
        get_state().unknownIds = 0
        if "main" in sys.modules:
            import main

            importlib.reload(main)
        else:
            import main

    def toException(x):
        return Exception(x)

    js.window.evalRun = evalRun
    js.window.showTraceback = showTraceback
    js.window.toException = toException

    if hasattr(js.window, "dispatchEvent"):
        js.window.dispatchEvent(js.window.CustomEvent.new("smartpy_ready"))


def _init_jupyter_standard():
    """
    Initialize Jupyter Standard environment by loading SmartPy JavaScript modules.

    Suppose we are in a Jupyter environment if IPython is available.
    """
    if get_state().runtime != Runtime.NATIVE:
        raise Exception(
            "Cannot initialize Jupyter Standard environment in non-native Python"
        )
    try:
        from IPython.display import Javascript, display

        # Load and display the jupyter-web-components.js content directly
        js_content = get_wheel_file("jupyter-web-components.js")
        display(Javascript(js_content))
    except (ImportError, FileNotFoundError):
        pass


def _detect_runtime():
    """
    Detect runtime environment and initialize appropriate services.

    Detection logic:
    1. emscripten platform = JavaScript/browser execution
    2. Within browser: IPython availability = Jupyter Lite vs web IDE
    """
    state = get_state()

    # emscripten platform indicates JavaScript/WebAssembly in browser
    if sys.platform == "emscripten":
        # We're in browser (JavaScript). Now distinguish Jupyter Lite from web IDE
        try:
            # Jupyter Lite setup includes IPython, web IDE does not
            from IPython.display import HTML, display

            state.runtime = Runtime.JUPYTER_LITE
        except ImportError:
            # Web IDE context (no IPython available)
            state.runtime = Runtime.IDE
    else:
        state.runtime = Runtime.NATIVE


def init_runtime():
    _detect_runtime()
    state = get_state()

    if state.runtime == Runtime.NATIVE:
        _init_oasis()
        _init_canopy()
        _init_jupyter_standard()
    elif state.runtime == Runtime.IDE:
        _init_ide()
    elif state.runtime == Runtime.JUPYTER_LITE:
        _init_jupyter_lite()
    else:
        raise Exception("Unknown runtime")


def get_disabled_server():
    return os.environ.get("SMARTPY_DISABLE_SERVER") is not None


def get_debug():
    return os.environ.get("SMARTPY_DEBUG") is not None


def get_make_file_dependencies():
    return os.environ.get("SMARTPY_DEPENDENCIES_FILE")
