#! /usr/bin/env bash

function bluer_ai_git_increment_version() {
    local options=$1
    local do_diff=$(bluer_ai_option_int "$options" diff 0)

    python3 -m bluer_ai.plugins.git \
        increment_version \
        --repo_path $abcli_path_git/$(bluer_ai_git_get_repo_name) \
        "${@:2}"
    [[ $? -ne 0 ]] && return 1

    [[ "$do_diff" == 1 ]] &&
        bluer_ai_git diff

    return 0
}
