from typing import List

from bluer_options.terminal import show_usage


def help_perform_action(
    tokens: List[str],
    mono: bool,
) -> str:
    options = "action=<action-name>,plugin=<plugin-name>"

    return show_usage(
        [
            "@perform_action",
            f"[{options}]",
            "<args>",
        ],
        "perform the action.",
        mono=mono,
    )
