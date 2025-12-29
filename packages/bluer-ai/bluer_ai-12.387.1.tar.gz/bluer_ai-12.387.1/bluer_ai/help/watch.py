from typing import List

from bluer_options.terminal import show_usage, xtra


def help_watch(
    tokens: List[str],
    mono: bool,
) -> str:
    options = "".join(
        [
            xtra("~clear,dryrun,", mono=mono),
            "seconds=<seconds>",
        ]
    )

    return show_usage(
        [
            "@watch",
            f"[{options}]",
            "<command-line>",
        ],
        "watch <command-line>.",
        mono=mono,
    )
