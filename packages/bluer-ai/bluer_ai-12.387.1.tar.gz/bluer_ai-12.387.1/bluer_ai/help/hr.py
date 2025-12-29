from typing import List

from bluer_options.terminal import show_usage


def help_hr(
    tokens: List[str],
    mono: bool,
) -> str:
    return show_usage(
        [
            "@hr",
        ],
        "</hr>.",
        mono=mono,
    )
