from typing import List

from bluer_options.terminal import show_usage


def help_diagnose(
    tokens: List[str],
    mono: bool,
) -> str:
    return show_usage(
        [
            "@wifi",
            "diagnose",
        ],
        "diagnose wifi.",
        mono=mono,
    )


def help_get_ssid(
    tokens: List[str],
    mono: bool,
) -> str:
    return show_usage(
        [
            "@wifi",
            "get_ssid",
        ],
        "get wifi ssid.",
        mono=mono,
    )


help_functions = {
    "diagnose": help_diagnose,
    "get_ssid": help_get_ssid,
}
