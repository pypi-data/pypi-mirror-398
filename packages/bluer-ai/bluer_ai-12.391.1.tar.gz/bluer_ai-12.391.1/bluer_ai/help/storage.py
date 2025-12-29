from typing import List

from bluer_options.terminal import show_usage, xtra


def help_clear(
    tokens: List[str],
    mono: bool,
) -> str:
    options = "".join(
        [
            "cloud",
            xtra(",~dryrun,", mono=mono),
            "public",
        ]
    )

    return show_usage(
        [
            "@storage",
            "clear",
            f"[{options}]",
        ],
        "clear storage.",
        mono=mono,
    )


def help_status(
    tokens: List[str],
    mono: bool,
) -> str:
    options = "count=<10>,depth=<2>"

    return show_usage(
        [
            "@storage",
            "status",
            f"[{options}]",
        ],
        "show storage status.",
        mono=mono,
    )


help_functions = {
    "clear": help_clear,
    "status": help_status,
}
