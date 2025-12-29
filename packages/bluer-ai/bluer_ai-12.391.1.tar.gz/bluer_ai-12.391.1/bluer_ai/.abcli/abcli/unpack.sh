#! /usr/bin/env bash

function bluer_ai_unpack_repo_name() {
    local repo_name=${1:-bluer-ai}

    if alias "$repo_name" &>/dev/null; then
        repo_name=$(alias "$repo_name" | sed -E "s/^alias $repo_name='(.*)'$/\1/")
    fi

    repo_name=$(echo "$repo_name" | tr _ -)

    [[ "$repo_name" == "." ]] &&
        repo_name=$(bluer_ai_git_get_repo_name)

    echo $repo_name
}
