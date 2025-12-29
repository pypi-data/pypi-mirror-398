from typing import List

from bluer_options.terminal import show_usage, xtra


def help_(
    tokens: List[str],
    mono: bool,
) -> str:
    options = xtra("yes | no | empty | non-empty", mono=mono)

    return show_usage(
        [
            "@assert",
            "<this>",
            "<that>",
            f"[{options}]",
        ],
        "assert <this> <?> <that>.",
        mono=mono,
    )


def help_list(
    tokens: List[str],
    mono: bool,
) -> str:
    return show_usage(
        [
            "@assert",
            "list",
            "<this,that,which>",
            "<that,this,what>",
        ],
        "assert that the two lists are identical.",
        mono=mono,
    )


help_functions = {
    "": help_,
    "list": help_list,
}
