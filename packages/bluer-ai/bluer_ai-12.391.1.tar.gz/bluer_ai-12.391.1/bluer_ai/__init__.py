import os

NAME = "bluer_ai"

ICON = "🌀"

DESCRIPTION = f"{ICON} A language to speak AI."

VERSION = "12.391.1"

REPO_NAME = "bluer-ai"

MARQUEE = "https://github.com/kamangir/assets/blob/main/awesome-bash-cli/marquee-2024-10-26.jpg?raw=true"


def fullname() -> str:
    bluer_ai_git_branch = os.getenv("bluer_ai_git_branch", "")
    return "{}-{}{}".format(
        NAME,
        VERSION,
        f"-{bluer_ai_git_branch}" if bluer_ai_git_branch else "",
    )
