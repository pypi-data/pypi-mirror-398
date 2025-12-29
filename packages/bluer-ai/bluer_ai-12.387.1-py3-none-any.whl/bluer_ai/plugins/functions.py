from typing import List
import glob
import os

# https://chatgpt.com/c/683d39ac-34a8-8005-b780-71a6d2253ea9
try:
    from importlib.metadata import distributions
except ImportError:
    # for Python < 3.8
    from importlib_metadata import distributions  # type: ignore

from bluer_objects import file, path
from bluer_objects.env import abcli_path_git


def get_plugin_name(repo_name: str) -> str:
    return "abcli" if repo_name == "awesome-bash-cli" else repo_name.replace("-", "_")


def get_module_name(repo_name: str) -> str:
    list_of_candidates = sorted(
        file.path(filename)
        for filename in glob.glob(
            os.path.join(abcli_path_git, repo_name, "**/__init__.py"),
            recursive=True,
        )
    )

    if not list_of_candidates:
        return "no-module-found"

    return path.name(list_of_candidates[0])


def list_of_external(repo_names=False) -> List[str]:
    output = sorted(
        [
            repo_name
            for repo_name in [
                path.name(path_)
                for path_ in glob.glob(os.path.join(abcli_path_git, "*/"))
            ]
            if repo_name not in ["awesome-bash-cli", "bluer-ai"]
            and path.exists(
                os.path.join(
                    abcli_path_git,
                    repo_name,
                    get_module_name(repo_name),
                    ".abcli",
                )
            )
        ]
    )

    if not repo_names:
        output = [repo_name.replace("-", "_") for repo_name in output]

    return output


def list_of_installed(return_path: bool = False) -> List[str]:
    output = []

    for dist in distributions():
        try:
            name = dist.metadata.get("Name")
            if not name:
                continue

            key = name.lower().replace("-", "_")
            if key in ["abcli", "bluer_ai"]:
                continue

            # Estimate install path
            root_path = str(dist.locate_file(""))
            if "git" in root_path.split(os.sep):
                continue

            module_bash_folder = os.path.join(root_path, key, ".abcli")
            if not os.path.exists(module_bash_folder):
                continue

            output.append(module_bash_folder if return_path else key)

        except Exception:
            continue

    return output
