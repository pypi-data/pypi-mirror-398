from typing import List

from bluer_options.terminal import show_usage


def help_wait(
    tokens: List[str],
    mono: bool,
) -> str:
    return show_usage(
        [
            "@wait",
            "[<message>]",
        ],
        "wait with <message>.",
        mono=mono,
    )
