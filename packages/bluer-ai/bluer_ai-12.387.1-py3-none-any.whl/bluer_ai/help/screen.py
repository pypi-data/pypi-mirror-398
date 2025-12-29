from typing import List

from bluer_options.terminal import show_usage


def help_(
    tokens: List[str],
    mono: bool,
) -> str:
    return show_usage(
        [
            "@screen",
            "[<screen-name>]",
        ],
        "start a screen.",
        mono=mono,
    )


def help_detach(
    tokens: List[str],
    mono: bool,
) -> str:
    return show_usage(
        [
            "@screen",
            "detach",
            "<screen-name>",
        ],
        "detach <screen-name>.",
        mono=mono,
    )


def help_list(
    tokens: List[str],
    mono: bool,
) -> str:
    return show_usage(
        [
            "@screen",
            "list",
        ],
        "list screens.",
        mono=mono,
    )


def help_resume(
    tokens: List[str],
    mono: bool,
) -> str:
    return show_usage(
        [
            "@screen",
            "resume",
            "<screen-name>",
        ],
        "resume <screen-name>",
        mono=mono,
    )


help_functions = {
    "": help_,
    "detach": help_detach,
    "list": help_list,
    "resume": help_resume,
}
