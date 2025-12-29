#! /usr/bin/env bash

function bluer_ai_pypi_browse() {
    local options=$1
    local plugin_name=$(bluer_ai_option "$options" plugin bluer_ai)
    local do_token=$(bluer_ai_option_int "$options" token 0)

    local module_name=$(bluer_ai_get_module_name_from_plugin $plugin_name)

    local url="https://pypi.org/project/$module_name/"
    [[ "$do_token" == 1 ]] &&
        url="https://pypi.org/manage/account/token/"

    bluer_ai_browse $url

    [[ "$do_token" == 0 ]] && return 0

    local pyrc_filename=$HOME/.pypirc
    [[ ! -f "$pyrc_filename" ]] &&
        cp -v \
            $abcli_path_assets/pypi/.pypirc \
            $pyrc_filename

    bluer_ai_code $pyrc_filename
}
