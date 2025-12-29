from typing import List

from bluer_options.terminal import show_usage


def help_add(
    tokens: List[str],
    mono: bool,
) -> str:
    return show_usage(
        [
            "@ssh",
            "add",
            "<filename>",
        ],
        "ssh add <filename>.",
        mono=mono,
    )


def help_copy_id(
    tokens: List[str],
    mono: bool,
) -> str:
    return show_usage(
        [
            "@ssh",
            "copy_id",
            "<filename>",
            "jetson_nano | rpi",
            "<machine-name>",
        ],
        "ssh copy-id <filename> to <machine-name>.",
        mono=mono,
    )


def help_ec2(
    tokens: List[str],
    mono: bool,
) -> str:
    options = "region=<region_1>,user=<ec2-user|ubuntu>,vnc"

    return show_usage(
        [
            "@ssh",
            "ec2",
            "<ip-address>",
            f"[{options}]",
        ],
        "ssh to <ip-address>.",
        mono=mono,
    )


def help_sbc(
    tokens: List[str],
    mono: bool,
) -> str:
    return show_usage(
        [
            "@ssh",
            "jetson_nano | rpi",
            "<machine-name>",
        ],
        "ssh to <machine-name>.",
        mono=mono,
    )


def help_keygen(
    tokens: List[str],
    mono: bool,
) -> str:
    return show_usage(
        [
            "@ssh",
            "keygen",
            "[<filename>]",
        ],
        "keygen <filename>.",
        mono=mono,
    )


help_functions = {
    "add": help_add,
    "copy_id": help_copy_id,
    "ec2": help_ec2,
    "sbc": help_sbc,
    "keygen": help_keygen,
}
