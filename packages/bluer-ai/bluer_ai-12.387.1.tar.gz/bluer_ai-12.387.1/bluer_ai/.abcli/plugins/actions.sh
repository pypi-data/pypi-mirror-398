#! /usr/bin/env bash

function bluer_ai_perform_action() {
    local options=$1
    local action_name=$(bluer_ai_option "$options" action void)
    local plugin_name=$(bluer_ai_option "$options" plugin bluer_ai)

    local function_name=${plugin_name}_action_${action_name}

    [[ $(type -t $function_name) != "function" ]] &&
        return 0

    bluer_ai_log "✴️  action: $plugin_name: $action_name."
    $function_name "${@:2}"
}

function bluer_ai_action_git_before_push() {
    bluer_ai build_README
    [[ $? -ne 0 ]] && return 1

    [[ "$(bluer_ai_git get_branch)" != "main" ]] &&
        return 0

    bluer_ai pypi build
}
