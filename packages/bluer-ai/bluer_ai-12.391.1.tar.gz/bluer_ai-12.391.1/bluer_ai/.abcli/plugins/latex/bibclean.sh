#! /usr/bin/env bash

function bluer_ai_latex_bibclean() {
    local options=$1
    local do_install=$(bluer_ai_option_int "$options" install 0)

    [[ "$do_install" == 1 ]] &&
        bluer_ai_latex_install $options

    local filename=${2:-void}

    local temp_filename=$abcli_path_temp/bibclean-$(bluer_ai_string_timestamp_short).bib

    bluer_ai_eval ,$options \
        bibclean $filename >$temp_filename

    mv -v $temp_filename $filename
}
