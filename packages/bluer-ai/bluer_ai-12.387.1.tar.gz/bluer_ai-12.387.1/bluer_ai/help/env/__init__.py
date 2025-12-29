from typing import List

from bluer_options.terminal import show_usage

from bluer_ai.help.env.backup import help_functions as help_backup
from bluer_ai.help.env.dot import help_functions as help_dot


def help_(
    tokens: List[str],
    mono: bool,
) -> str:
    return show_usage(
        [
            "@env",
            "[keyword]",
        ],
        "show environment variables.",
        mono=mono,
    )


help_functions = {
    "": help_,
    "backup": help_backup,
    "dot": help_dot,
}
