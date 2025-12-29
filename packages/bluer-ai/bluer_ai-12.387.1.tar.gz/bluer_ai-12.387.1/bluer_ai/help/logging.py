from typing import List

from bluer_options.terminal import show_usage, xtra


def help_cat(
    tokens: List[str],
    mono: bool,
) -> str:
    return show_usage(
        [
            "@cat",
            "<filename>",
        ],
        "cat <filename>.",
        mono=mono,
    )


def help_log(
    tokens: List[str],
    mono: bool,
) -> str:
    return show_usage(
        [
            "@log",
            "<message>",
        ],
        "log message.",
        mono=mono,
    )


def help_log_error(
    tokens: List[str],
    mono: bool,
) -> str:
    return show_usage(
        [
            "@error",
            "<message>",
        ],
        "error <message>.",
        mono=mono,
    )


def help_log_list(
    tokens: List[str],
    mono: bool,
) -> str:
    args = [
        '[--before "list of"]',
        '[--after "items(s)"]',
        "[--delim space | <delim>]",
    ]

    return show_usage(
        [
            "@log::list",
            "<this,that>",
        ]
        + args,
        "log list.",
        mono=mono,
    )


def help_log_rm(
    tokens: List[str],
    mono: bool,
) -> str:
    return show_usage(
        [
            "@log",
            "rm",
        ],
        "rm the log.",
        mono=mono,
    )


def help_log_verbose(
    tokens: List[str],
    mono: bool,
) -> str:
    options = "on | off"

    return show_usage(
        [
            "@log",
            "verbose",
            f"[{options}]",
        ],
        "verbose logging on/off.",
        mono=mono,
    )


def help_log_watch(
    tokens: List[str],
    mono: bool,
) -> str:
    options = xtra("rpi", mono=mono)

    return show_usage(
        [
            "@log",
            "watch",
            f"[{options}]",
            "[<machine-name>]",
        ],
        "watch the log.",
        mono=mono,
    )


def help_log_warning(
    tokens: List[str],
    mono: bool,
) -> str:
    return show_usage(
        [
            "@warn",
            "<message>",
        ],
        "warn <message>.",
        mono=mono,
    )


help_functions = {
    "": help_log,
    "error": help_log_error,
    "warning": help_log_warning,
    "list": help_log_list,
    "rm": help_log_rm,
    "verbose": help_log_verbose,
    "watch": help_log_watch,
}
