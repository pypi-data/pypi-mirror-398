#! /usr/bin/env bash

function bluer_ai_git_create_branch() {
    local branch_name=$1
    if [[ -z "$branch_name" ]]; then
        bluer_ai_log_error "@git: create_brach: branch name not found."
        return 1
    fi

    local options=$2
    local do_offline=$(bluer_ai_option_int "$options" offline 0)
    local do_push=$(bluer_ai_option_int "$options" push 1)
    local do_increment_version=$(bluer_ai_option_int "$options" increment_version $(bluer_ai_not $do_push))
    local do_timestamp=$(bluer_ai_option_int "$options" timestamp 1)

    if [[ "$do_increment_version" == 1 ]]; then
        bluer_ai_git_increment_version
        [[ $? -ne 0 ]] && return 1
    fi

    [[ "$do_timestamp" == 1 ]] &&
        branch_name=$branch_name-$(bluer_ai_string_timestamp)

    if [[ "$do_offline" == 0 ]]; then
        git pull
        [[ $? -ne 0 ]] && return 1
    fi

    git checkout -b $branch_name
    [[ $? -ne 0 ]] && return 1

    if [[ "$do_offline" == 0 ]]; then
        git push origin $branch_name
        [[ $? -ne 0 ]] && return 1
    fi

    if [[ "$do_push" == 1 ]]; then
        bluer_ai_git_push \
            "start of $branch_name 🌀" \
            first,offline=$do_offline
    fi
}
