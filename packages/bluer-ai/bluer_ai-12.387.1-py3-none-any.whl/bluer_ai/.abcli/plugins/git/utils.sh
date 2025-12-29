#! /usr/bin/env bash

function bluer_ai_refresh_branch_and_version() {
    export bluer_ai_version=$(python3 -c "import bluer_ai; print(bluer_ai.VERSION)")

    export bluer_ai_git_branch=$(bluer_ai_git bluer-ai get_branch)

    export abcli_fullname=bluer_ai-$bluer_ai_version.$bluer_ai_git_branch
}
