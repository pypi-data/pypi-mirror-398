from typing import List

from bluer_options.terminal import show_usage


def help_after(
    tokens: List[str],
    mono: bool,
) -> str:
    return show_usage(
        [
            "bluer_ai_string_after",
            "<string>",
            "<substring>",
        ],
        "<string>.after(<substring>)",
        mono=mono,
    )


def help_before(
    tokens: List[str],
    mono: bool,
) -> str:
    return show_usage(
        [
            "bluer_ai_string_before",
            "<string>",
            "<substring>",
        ],
        "<string>.before(<substring>)",
        mono=mono,
    )


def help_random(
    tokens: List[str],
    mono: bool,
) -> str:
    args = [
        "[--float 1]",
        "[--int 1]",
        "[--length <8>]",
        "[--min <1.0>]",
        "[--max <100.0>]",
    ]

    return show_usage(
        [
            "@random",
        ]
        + args,
        "random float/int/string.",
        mono=mono,
    )


def help_timestamp(
    tokens: List[str],
    mono: bool,
) -> str:
    return show_usage(
        [
            "@timestamp",
        ],
        "timestamp.",
        mono=mono,
    )


def help_timestamp_short(
    tokens: List[str],
    mono: bool,
) -> str:
    return show_usage(
        [
            "@@timestamp",
        ],
        "short timestamp.",
        mono=mono,
    )


def help_today(
    tokens: List[str],
    mono: bool,
) -> str:
    args = [
        "[--include_time 1]",
        "[--unique 1]",
    ]

    return show_usage(
        [
            "@today",
        ]
        + args,
        "today.",
        mono=mono,
    )


help_functions = {
    "after": help_after,
    "before": help_before,
    "random": help_random,
    "timestamp": {
        "": help_timestamp,
        "short": help_timestamp_short,
    },
    "today": help_today,
}
