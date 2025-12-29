#! /usr/bin/env bash

function bluer_ai_git_pull() {
    local options=$1
    local do_all=$(bluer_ai_option_int "$options" all 1)
    local do_init=$(bluer_ai_option_int "$options" init 0)

    local abcli_fullname_before=$abcli_fullname

    if [ "$do_all" == 0 ]; then
        git pull
    else
        pushd $abcli_path_abcli >/dev/null
        git pull

        local repo
        for repo in bluer-options $(bluer_ai_plugins list_of_external --delim space --log 0 --repo_names 1); do
            if [ -d "$abcli_path_git/$repo" ]; then
                bluer_ai_log $repo
                cd ../$repo
                git pull
                git config pull.rebase false
            fi
        done
        popd >/dev/null
    fi

    [[ "$do_init" == 0 ]] && return 0

    bluer_ai_refresh_branch_and_version

    if [ "$abcli_fullname" == "$abcli_fullname_before" ]; then
        bluer_ai_log "no version change: $abcli_fullname"
        return
    fi

    bluer_ai_log "version change: $abcli_fullname_before -> $abcli_fullname"
    bluer_ai_init
}
