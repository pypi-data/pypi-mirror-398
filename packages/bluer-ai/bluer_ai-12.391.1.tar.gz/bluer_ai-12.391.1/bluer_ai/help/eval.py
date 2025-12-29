from typing import List

from bluer_options.terminal import show_usage, xtra


def options(mono: bool):
    return xtra(
        "background,dryrun,~log,path=<path>",
        mono=mono,
    )


def help_eval(
    tokens: List[str],
    mono: bool,
) -> str:
    return show_usage(
        [
            "@eval",
            f"[{options(mono=mono)}]",
            "<command-line>",
        ],
        "eval <command-line>.",
        mono=mono,
    )
