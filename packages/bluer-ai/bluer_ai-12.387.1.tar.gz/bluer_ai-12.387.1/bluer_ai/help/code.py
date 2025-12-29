from typing import List

from bluer_options.terminal import show_usage


def help_code(
    tokens: List[str],
    mono: bool,
) -> str:
    return show_usage(
        [
            "@code",
            "<filename>",
        ],
        "code <filename>.",
        mono=mono,
    )
