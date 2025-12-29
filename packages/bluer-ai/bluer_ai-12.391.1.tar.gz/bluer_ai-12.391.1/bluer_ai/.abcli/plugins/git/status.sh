#! /usr/bin/env bash

function bluer_ai_git_status() {
    local options=$1
    local do_all=$(bluer_ai_option_int "$options" all 1)

    if [[ "$do_all" == 0 ]]; then
        bluer_ai_eval path=$abcli_path_git/$(bluer_ai_git_get_repo_name),~log \
            git status
        return
    fi

    pushd $abcli_path_git >/dev/null
    local repo_name
    for repo_name in $(ls -d */); do
        bluer_ai_log $repo_name

        cd $repo_name
        git status
        cd ..
    done
    popd >/dev/null
}
