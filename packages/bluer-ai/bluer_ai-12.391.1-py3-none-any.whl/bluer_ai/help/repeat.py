from typing import List

from bluer_options.terminal import show_usage

from bluer_ai.help.eval import options as eval_options


def help_repeat(
    tokens: List[str],
    mono: bool,
) -> str:
    options = "".join(
        [
            "count=<count>,",
            eval_options(mono=mono),
        ]
    )

    return show_usage(
        [
            "@repeat",
            f"[{options}]",
            "<command-line>",
        ],
        "repeat <command-line>.",
        mono=mono,
    )
