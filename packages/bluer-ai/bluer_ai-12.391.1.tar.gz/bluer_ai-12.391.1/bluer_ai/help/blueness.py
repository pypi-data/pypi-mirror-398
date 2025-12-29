from typing import List

from bluer_options.terminal import show_usage, xtra


def help_blueness(
    tokens: List[str],
    mono: bool,
) -> str:
    return show_usage(
        [
            "blueness",
            "upgrade",
        ],
        "upgrade blueness 🌀.",
        mono=mono,
    )
