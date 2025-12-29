import os

from bluer_options.help.functions import get_help
from bluer_objects import file, README

from bluer_ai import NAME, VERSION, ICON, REPO_NAME
from bluer_ai.help.functions import help_functions


def build():
    return all(
        README.build(
            path=os.path.join(file.path(__file__), path),
            ICON=ICON,
            NAME=NAME,
            VERSION=VERSION,
            REPO_NAME=REPO_NAME,
            MODULE_NAME=NAME,
            help_function=lambda tokens: get_help(
                tokens,
                help_functions,
                mono=True,
            ),
        )
        for path in [
            "..",
            # @ai
            "docs/aliases/conda.md",
            "docs/aliases/git.md",
            "docs/aliases/gpu.md",
            "docs/aliases/init.md",
            "docs/aliases/latex.md",
            "docs/aliases/logging.md",
            "docs/aliases/plugins.md",
            "docs/aliases/pypi.md",
            "docs/aliases/random.md",
            "docs/aliases/screen.md",
            "docs/aliases/seed.md",
            "docs/aliases/ssh.md",
            "docs/aliases/terraform.md",
            "docs/aliases/today.md",
            "docs/aliases/wifi.md",
            # @options
            "docs/aliases/assert.md",
            "docs/aliases/badge.md",
            "docs/aliases/browse.md",
            "docs/aliases/cat.md",
            "docs/aliases/code.md",
            "docs/aliases/env.md",
            "docs/aliases/eval.md",
            "docs/aliases/help.md",
            "docs/aliases/hr.md",
            "docs/aliases/list.md",
            "docs/aliases/not.md",
            "docs/aliases/open.md",
            "docs/aliases/option.md",
            "docs/aliases/pause.md",
            "docs/aliases/pylint.md",
            "docs/aliases/pytest.md",
            "docs/aliases/repeat.md",
            "docs/aliases/sleep.md",
            "docs/aliases/test.md",
            "docs/aliases/timestamp.md",
            "docs/aliases/wait.md",
            "docs/aliases/watch.md",
            # @objects
            "docs/aliases/select.md",
            "docs/aliases/storage.md",
        ]
    )
