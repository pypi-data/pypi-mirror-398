from typing import List

from bluer_options.terminal import show_usage, xtra


def help_pytest(
    tokens: List[str],
    mono: bool,
    plugin_name: str = "bluer_ai",
) -> str:
    options = "".join(
        [
            "list",
            xtra(
                ",dryrun,~log,show_warning,~verbose",
                mono=mono,
            ),
        ]
    )

    callable = f"{plugin_name} pytest"

    if plugin_name == "bluer_ai":
        options = f"{options},plugin=<plugin-name>"
        callable = "@pytest"

    return show_usage(
        callable.split(" ")
        + [
            f"[{options}]",
            "[filename.py|filename.py::test]",
        ],
        f"pytest {plugin_name}.",
        mono=mono,
    )
