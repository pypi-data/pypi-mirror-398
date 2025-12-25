import inspect
import os
import pathlib
from os.path import dirname, join


def get_wheel_file(file_name):
    """Load and evaluate a JavaScript file."""
    file_path = join(dirname(dirname(__file__)), "static", file_name)
    with open(file_path, "r") as file:
        return file.read()


def make_relative(path):
    cwd = os.getcwd()
    try:
        return pathlib.Path(path).relative_to(cwd)
    except ValueError:
        return path


def expand_resolve(pth):
    try:
        return pathlib.Path(pth).expanduser().resolve()
    except RuntimeError:
        return pth


# -- LineNo --


class LineNo:
    def __init__(self, filename, line_no):
        self.filename = make_relative(filename)
        self.line_no = line_no

    def export(self):
        return f'("{self.filename}" {self.line_no})'


def get_file_line_no(line_no=None):
    if line_no is not None:
        return line_no
    frame = inspect.currentframe().f_back
    smartpy_path = pathlib.Path(__file__).parent.parent.resolve()

    while frame:
        fn = frame.f_code.co_filename
        file_path = pathlib.Path(fn).resolve()

        try:
            # This will raise ValueError if file_path is not within smartpy_path
            file_path.relative_to(smartpy_path)
            is_within_smartpy = True
        except ValueError:
            is_within_smartpy = False

        if not is_within_smartpy and "<frozen " not in fn and "init" != fn:
            if ":" in fn:
                fn = fn[fn.rindex(":") + 1 :]
            fn = os.path.relpath(fn)
            return LineNo(fn, frame.f_lineno)
        frame = frame.f_back
    return LineNo("", -1)


def get_file_line_no_direct():
    frame = inspect.currentframe()
    frame = frame.f_back
    frame = frame.f_back
    fn = frame.f_code.co_filename
    fn = os.path.relpath(fn)
    return LineNo(fn, frame.f_lineno)


def get_id_from_line_no():
    l = get_file_line_no()
    if not l.filename:
        return str(l.line_no)
    return (
        l.filename.replace("/", " ").replace(".py", "").strip("<>./,'").split()[-1]
        + "_"
        + str(l.line_no)
    )


def pretty_line_no():
    line_no = get_file_line_no()
    if line_no.filename:
        of_file = f" of {line_no.filename}"
    else:
        of_file = ""
    line_no = line_no.line_no
    return "(line %i%s)" % (line_no, of_file)
