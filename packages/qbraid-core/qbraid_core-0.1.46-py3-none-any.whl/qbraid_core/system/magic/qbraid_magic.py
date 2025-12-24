# Copyright (c) 2025, qBraid Development Team
# All rights reserved.

"""
Module defining custom qBraid IPython magic commands.

"""

import os
import shlex
import subprocess
import sys
import warnings
from pathlib import Path
from typing import Optional

from IPython.core.magic import Magics, line_magic, magics_class

from qbraid_core.services.chat.client import ChatClient

CHAT_FLAG_MAP = {"-m": "--model", "-f": "--format", "-s": "--stream", "-h": "--help"}

LANGUAGES = [
    "python",
    "qasm",
    "javascript",
    "java",
    "c",
    "c++",
    "c#",
    "ruby",
    "php",
    "go",
    "swift",
    "kotlin",
    "rust",
    "typescript",
    "html",
    "css",
    "sql",
    "bash",
    "powershell",
    "yaml",
    "json",
    "xml",
    "markdown",
    "r",
    "matlab",
    "perl",
    "scala",
    "haskell",
    "lua",
    "dart",
    "groovy",
    "objective-c",
    "vb.net",
    "f#",
    "clojure",
    "erlang",
    "elixir",
    "ocaml",
    "julia",
    "lisp",
    "prolog",
    "fortran",
    "pascal",
    "cobol",
    "assembly",
    "latex",
    "graphql",
    "dockerfile",
    "makefile",
    "cmake",
    "vimscript",
    "vim",
    "tex",
]


def strip_code_fence(s: str) -> str:
    """
    Strips leading and trailing Markdown code fences from a string.

    Supports leading fences like ```python, ```qasm, or ``` with or without a language specifier.

    Args:
        s (str): The input string.

    Returns:
        str: The string without leading and trailing code fences if they exist.
    """
    if not (s.startswith("```") and s.endswith("```")):
        return s

    matched_lang = None
    for lang in LANGUAGES:
        if s.startswith(f"```{lang}"):
            matched_lang = lang
            break

    matched_lang = matched_lang or ""
    s = s.removeprefix(f"```{matched_lang}")
    s = s.removesuffix("```")

    return s.strip()


def extract_model(command: list[str]) -> tuple[Optional[str], list[str]]:
    """Extract the model argument and return the model and modified command."""
    for i, arg in enumerate(command):
        if CHAT_FLAG_MAP.get(arg, arg) == "--model":
            if i + 1 < len(command):
                return command[i + 1], [x for x in command if x not in {arg, command[i + 1]}]
            raise ValueError("Model flag provided without a model name.")
    return None, command


def parse_magic_chat_command(command: list[str]) -> Optional[dict[str, Optional[str]]]:
    """Parse the qbraid chat command and return the prompt, model, and response format."""
    if not (5 <= len(command) <= 8) or command[:2] != ["qbraid", "chat"]:
        return None

    command_set = set(command)
    if command_set & {"--help", "-h"} or command[-1] in {"--model", "-m"}:
        return None

    new_command = command[2:]
    format_flags = {CHAT_FLAG_MAP.get(arg, arg) for arg in new_command} & {"--format", "-f"}
    if format_flags and not (
        {"--format", "code"}.issubset(new_command) or {"-f", "code"}.issubset(new_command)
    ):
        return None

    model, new_command = extract_model(new_command)
    new_command = [x for x in new_command if x not in {"--stream", "-s", "--format", "-f", "code"}]

    if len(new_command) != 2 or new_command[0] not in {"--prompt", "-p"}:
        return None

    if {"--stream", "-s"} & command_set:
        warnings.warn("The --stream option is not supported in this context. Ignoring it.")

    return {"prompt": new_command[1], "model": model, "response_format": "code"}


@magics_class
class SysMagics(Magics):
    """
    Custom IPython Magics class to allow running
    qBraid-CLI commands from within Jupyter notebooks.

    """

    @staticmethod
    def restore_env_var(var_name: str, original_value: Optional[str]) -> None:
        """
        Restore or remove an environment variable based on its original value.
        """
        if original_value is None:
            os.environ.pop(var_name, None)
        else:
            os.environ[var_name] = original_value

    @line_magic
    def qbraid(self, line):
        """
        Executes qBraid-CLI command using the sys.executable
        from a Jupyter Notebook kernel.
        """
        original_path = os.getenv("PATH")
        original_show_progress = os.getenv("QBRAID_CLI_SHOW_PROGRESS")
        python_dir = str(Path(sys.executable).parent)

        try:
            os.environ["PATH"] = python_dir + os.pathsep + original_path
            os.environ["QBRAID_CLI_SHOW_PROGRESS"] = "false"

            command = ["qbraid"] + shlex.split(line)
            chat_command_args = parse_magic_chat_command(command)

            if chat_command_args:
                client = ChatClient()

                content = client.chat(**chat_command_args)

                code = strip_code_fence(content)

                self.shell.set_next_input(code)
            else:
                if (
                    len(command) >= 5
                    and command[1] == "chat"
                    and ("--stream" in command[2:] or "-s" in command[2:])
                ):
                    warnings.warn(
                        "The --stream option is not supported in this context. Ignoring it."
                    )
                subprocess.run(command, check=True)

        finally:
            self.restore_env_var("PATH", original_path)
            self.restore_env_var("QBRAID_CLI_SHOW_PROGRESS", original_show_progress)


def load_ipython_extension(ipython):
    """Load the extension in IPython."""
    ipython.register_magics(SysMagics)
