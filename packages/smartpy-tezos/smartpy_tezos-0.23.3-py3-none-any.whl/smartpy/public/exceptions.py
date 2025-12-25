"""
Public SmartPy exceptions that users may encounter and handle.
"""


class FailwithException(Exception):
    def __init__(self, value, line_no, message, expansion):
        self.value = value
        self.line_no = line_no
        self.message = message
        self.expansion = expansion

    def __str__(self):
        code = (
            "    (source code not available)"
            if self.line_no[2] is None
            else self.line_no[2]
        )
        expansion = "" if self.expansion is None else f"{self.expansion}"
        return f"(SmartPy)\n  File \"{self.line_no[0]}\", line {self.line_no[1]}, in <module>\n{code}\nReachedFailwith: '{self.value}'{expansion}"


class RuntimeException(Exception):
    def __init__(self, line_no, message):
        self.line_no = line_no
        self.message = message

    def __str__(self):
        code = (
            "    (source code not available)"
            if self.line_no[2] is None
            else self.line_no[2]
        )
        return f'(SmartPy)\n  File "{self.line_no[0]}", line {self.line_no[1]}, in <module>\n    {code.strip()}\n{self.message}'


class TypeError_(Exception):
    def __init__(self, line_no, message):
        self.line_no = line_no
        self.message = message

    def __str__(self):
        code = (
            "(source code not available)"
            if self.line_no[2] is None
            else self.line_no[2].lstrip()
        )
        return f'(SmartPy)\n  File "{self.line_no[0]}", line {self.line_no[1]}, in <module>\n    {code.strip()}\n{self.message}'
