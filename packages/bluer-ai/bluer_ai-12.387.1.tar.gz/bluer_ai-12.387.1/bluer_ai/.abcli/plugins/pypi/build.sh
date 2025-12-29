#! /usr/bin/env bash

function bluer_ai_pypi_build() {
    local options=$1

    local plugin_name=$(bluer_ai_option "$options" plugin bluer_ai)
    local do_install=$(bluer_ai_option_int "$options" install 0)
    local do_upload=$(bluer_ai_option_int "$options" upload 1)
    local do_browse=$(bluer_ai_option_int "$options" browse 0)
    local rm_dist=$(bluer_ai_option_int "$options" rm_dist 1)

    [[ "$do_install" == 1 ]] &&
        bluer_ai_pypi_install

    local repo_name=$(bluer_ai_unpack_repo_name $plugin_name)
    if [[ ! -d "$abcli_path_git/$repo_name" ]]; then
        bluer_ai_log "@pypi: build: $repo_name: repo not found."
        return 1
    fi

    bluer_ai_log "pypi: building $plugin_name ($repo_name)..."

    pushd $abcli_path_git/$repo_name >/dev/null

    python3 -m build
    [[ $? -ne 0 ]] && return 1

    [[ "$do_upload" == 1 ]] &&
        twine upload dist/*

    [[ "$rm_dist" == 1 ]] &&
        rm -v dist/*

    popd >/dev/null

    [[ "$do_browse" == 1 ]] &&
        bluer_ai_pypi_browse "$@"

    return 0
}
