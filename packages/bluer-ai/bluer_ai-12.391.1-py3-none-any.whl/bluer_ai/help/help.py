from typing import List

from bluer_options.terminal import show_usage


def help_help(
    tokens: List[str],
    mono: bool,
) -> str:
    return show_usage(
        [
            "@help",
            "<command>",
        ],
        "show help for <command>.",
        mono=mono,
    )
