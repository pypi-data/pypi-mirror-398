from typing import List

from bluer_options.terminal import show_usage, xtra


def help_build_README(
    tokens: List[str],
    mono: bool,
    plugin_name: str = "bluer_ai",
) -> str:
    options = "push"

    callable = f"{plugin_name} build_README"

    if plugin_name == "bluer_ai":
        options = f"{options},plugin=<plugin-name>"
        callable = "@build_README"

    return show_usage(
        callable.split(" ")
        + [
            f"[{options}]",
        ],
        f"build {plugin_name}/README.md.",
        mono=mono,
    )
