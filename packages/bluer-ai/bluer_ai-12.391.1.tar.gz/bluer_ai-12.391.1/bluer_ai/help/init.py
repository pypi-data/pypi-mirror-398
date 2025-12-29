from typing import List

from bluer_options.terminal import show_usage, xtra


def help_init(
    tokens: List[str],
    mono: bool,
) -> str:
    what = xtra("<plugin-name> | all | clear", mono=mono)

    options = xtra("clear,~terraform", mono=mono)

    return show_usage(
        [
            "@init",
            f"[{what}]",
            f"[{options}]",
        ],
        "init.",
        mono=mono,
    )
