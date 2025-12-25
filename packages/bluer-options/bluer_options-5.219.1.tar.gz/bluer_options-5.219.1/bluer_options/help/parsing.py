import os
from typing import List

list_of_modules: List[str] = [
    "abcli",
    "bluer_agent",
    "bluer_ai",
    "bluer_algo",
    "bluer_flow",
    "bluer_geo",
    "bluer_journal",
    "bluer_options",
    "bluer_objects",
    "bluer_plugin",
    "bluer_sandbox",
    "bluer_sbc",
    "bluer_ugv",
    "giza",
] + [
    item
    for item in os.getenv(
        "BLUE_OPTIONS_HELP_MODULE_LIST",
        "",
    ).split("+")
    if item
]


def get_callable_module(
    callable: str,
    module_name_check: bool = True,
) -> str:
    for module in list_of_modules:
        if callable.startswith(module):
            return (
                os.getenv(f"{module}_module_name", module)
                if module_name_check
                else module
            )

    return callable


def get_callable_suffix(callable: str) -> str:
    module = get_callable_module(
        callable,
        module_name_check=False,
    )

    suffix = callable.split(module)[1]

    if suffix.startswith("_"):
        suffix = suffix[1:]

    return suffix
