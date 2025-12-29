#! /usr/bin/env bash

function bluer_ai_plugins_install() {
    local plugin_name=${1:-all}

    if [[ "$plugin_name" == all ]]; then
        pushd $abcli_path_git >/dev/null
        for dir in */; do
            if ! find "$dir" -type d -name ".abcli" -print -quit | read; then
                continue
            fi

            bluer_ai_log "$dir ..."

            cd $dir
            pip3 install -e .
            pip3 install -r requirements.txt
            cd ..
        done
        popd >/dev/null
        return
    fi

    local repo_name=$(bluer_ai_get_repo_name_from_plugin $plugin_name)
    if [[ -z "$repo_name" ]]; then
        bluer_ai_log_error "@plugins: install: $plugin_name: plugin not found."
        return 1
    fi

    bluer_ai_log "installing $plugin_name from $repo_name"

    pushd $abcli_path_git/$repo_name >/dev/null
    pip3 install -e .
    pip3 install -r requirements.txt
    popd >/dev/null
}
