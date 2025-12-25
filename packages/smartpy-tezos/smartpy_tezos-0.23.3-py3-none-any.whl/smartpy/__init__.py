# Copyright 2025 - present Trilitech Limited, 2022-2024 Morum LLC, 2019-2022 Smart Chain Arena LLC

import atexit
import importlib
import importlib.metadata
import sys
import traceback

import smartpy.public.scenario_utils as scenario_utils
import smartpy.stdlib
from smartpy.deprecated import *
from smartpy.internal.module_elements import View
from smartpy.internal.modules import Module, ParseKind
from smartpy.internal.state import init_state
from smartpy.internal.utils import LineNo, get_file_line_no
from smartpy.platform.runtime import get_debug, get_disabled_server, init_runtime
from smartpy.platform.services import ParseKind
from smartpy.platform.services import interact as _interact
from smartpy.public.exceptions import FailwithException, RuntimeException, TypeError_
from smartpy.public.instantiate_from_metadata import *
from smartpy.public.metadata import *
from smartpy.public.scenario import (
    SimulationMode,
    add_test,
    module,
    test_account,
    test_scenario,
)
from smartpy.public.syntax import *
from smartpy.public.types import *
from smartpy.stdlib import STDLIB_MODULES

__version__ = importlib.metadata.version("smartpy-tezos")


def __getattr__(name):
    """Deprecated: Makes the stdlib modules available directly like `sp.utils`.

    This is deprecated in favour of sp.stdlib.utils, etc. and will be removed in a future version.
    """
    # Handle stdlib attributes dynamically
    if name in STDLIB_MODULES:
        return getattr(smartpy.stdlib, name)


init_state()
init_runtime()


@atexit.register
def shutdown():
    if not get_disabled_server():
        _interact({"request": "exit"})


max = spmax
min = spmin


# -- Handling exceptions --
def scrub_traceback(tb):
    while tb and tb.tb_frame.f_code.co_filename == __file__:
        tb = tb.tb_next
    if tb:
        tb.tb_next = scrub_traceback(tb.tb_next)
    return tb


def handle_exception(exc_type, exc_value, exc_traceback):
    if not get_debug():
        exc_traceback = scrub_traceback(exc_traceback)
    tb_list = traceback.extract_tb(exc_traceback)
    print("Traceback (most recent call last):", file=sys.stderr)
    for item in tb_list:
        print(
            f'  File "{item.filename}", line {item.lineno}, in {item.name}\n    {item.line}',
            file=sys.stderr,
        )
    print(f"{exc_type.__name__}: {exc_value}", file=sys.stderr)


sys.excepthook = handle_exception
