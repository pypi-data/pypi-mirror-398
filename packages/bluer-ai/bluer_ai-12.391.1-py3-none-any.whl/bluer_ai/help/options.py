from typing import List

from bluer_options.terminal import show_usage


def help_(
    tokens: List[str],
    mono: bool,
) -> str:
    return show_usage(
        [
            "@option",
            '"$options"',
            "<keyword>",
            "[<default>]",
        ],
        "get $options[<keyword>].",
        mono=mono,
    )


def help_choice(
    tokens: List[str],
    mono: bool,
) -> str:
    return show_usage(
        [
            "@option::choice",
            '"$options"',
            "<keyword-1,keyword-2,keyword-3>",
            "[<default>]",
        ],
        "return <keyword-*> that is in $options.",
        mono=mono,
    )


def help_int(
    tokens: List[str],
    mono: bool,
) -> str:
    return show_usage(
        [
            "@option::int",
            '"$options"',
            "<keyword>",
            "[<default>]",
        ],
        "get int($options[<keyword>]).",
        mono=mono,
    )


help_functions = {
    "": help_,
    "choice": help_choice,
    "int": help_int,
}
