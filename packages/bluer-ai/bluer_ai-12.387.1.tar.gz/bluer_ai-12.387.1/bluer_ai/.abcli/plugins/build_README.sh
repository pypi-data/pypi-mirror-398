#! /usr/bin/env bash

function bluer_ai_build_README() {
    local options=$1
    local plugin_name=$(bluer_ai_option "$options" plugin bluer_ai)
    local do_push=$(bluer_ai_option_int "$options" push 0)

    local repo_name=$(bluer_ai_unpack_repo_name $plugin_name)
    local module_name=$(bluer_ai_plugins get_module_name $repo_name)

    python3 -m $module_name \
        build_README \
        "${@:2}"
    [[ $? -ne 0 ]] && return 1

    if [[ "$do_push" == 1 ]]; then
        bluer_ai_git $repo_name push \
            "$(python3 -m $module_name version) build"
    else
        bluer_ai_git $repo_name status ~all
    fi
}
