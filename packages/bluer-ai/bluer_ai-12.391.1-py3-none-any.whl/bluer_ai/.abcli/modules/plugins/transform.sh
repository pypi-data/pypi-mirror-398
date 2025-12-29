#! /usr/bin/env bash

function bluer_ai_plugins_transform() {
    local repo_name=$1
    if [[ -z "$repo_name" ]]; then
        bluer_ai_log_error "@plugins: transform: $repo_name: repo not found."
        return 1
    fi
    local plugin_name=$(bluer_ai_plugin_name_from_repo $repo_name)

    if [[ ! -d "$abcli_path_git/$repo_name" ]]; then
        bluer_ai_log_error "@plugins: transform: $repo_name: repo not found."
        return 1
    fi

    bluer_ai_log "bluer-plugin -> $repo_name ($plugin_name)"

    pushd $abcli_path_git/$repo_name >/dev/null

    git mv bluer_plugin $plugin_name
    [[ $? -ne 0 ]] && return 1

    git mv \
        $plugin_name/.abcli/bluer_plugin.sh \
        $plugin_name/.abcli/$plugin_name.sh
    [[ $? -ne 0 ]] && return 1

    git mv \
        $plugin_name/docs/aliases/plugin-template.md \
        $plugin_name/docs/aliases/$plugin_name-template.md
    [[ $? -ne 0 ]] && return 1

    git mv \
        $plugin_name/docs/aliases/plugin.md \
        $plugin_name/docs/aliases/$plugin_name.md
    [[ $? -ne 0 ]] && return 1

    python3 -m bluer_ai.plugins \
        transform \
        --repo_name $repo_name \
        --plugin_name $plugin_name \
        "${@:2}"
}
