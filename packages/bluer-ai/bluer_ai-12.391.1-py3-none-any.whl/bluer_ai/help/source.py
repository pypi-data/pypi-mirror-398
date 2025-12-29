from typing import List

from bluer_options.terminal import show_usage

source_path_options = "ignore_error,~log"


def help_source_caller_suffix_path(
    tokens: List[str],
    mono: bool,
) -> str:
    options = source_path_options

    return show_usage(
        [
            "bluer_ai_source_caller_suffix_path",
            "<suffix>",
            f"[{options}]",
        ],
        "source <caller-path>/<suffix>.",
        mono=mono,
    )


def help_source_path(
    tokens: List[str],
    mono: bool,
) -> str:
    options = source_path_options

    return show_usage(
        [
            "bluer_ai_source_path",
            "<path>",
            f"[{options}]",
        ],
        "source <path>.",
        mono=mono,
    )
