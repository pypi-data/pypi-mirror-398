#! /usr/bin/env bash

function bluer_ai_initialize() {
    if [[ "$abcli_is_docker" == false ]] &&
        [[ "$abcli_is_aws_batch" == false ]]; then
        git config --global user.email "arash@kamangir.net"
        git config --global user.name "kamangir"
        git config --global credential.helper store
    fi

    [[ "$abcli_is_docker" == false ]] &&
        [[ "$abcli_is_in_notebook" == false ]] &&
        [[ "$abcli_is_aws_batch" == false ]] &&
        [[ "$abcli_is_github_workflow" == false ]] &&
        bluer_ai_add_ssh_keys

    export abcli_host_name=$(python3 -m bluer_options.host get --keyword name)

    [[ "$abcli_is_in_notebook" == true ]] && return

    bluer_ai_update_terminal
}
