from typing import List

from bluer_options.terminal import show_usage


def help_not(
    tokens: List[str],
    mono: bool,
) -> str:
    return show_usage(
        [
            "@not",
            "<var>",
        ],
        "not.",
        mono=mono,
    )
