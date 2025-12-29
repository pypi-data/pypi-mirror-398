#! /usr/bin/env bash

function bluer_ai_conda_rm() {
    local options=$1
    local environment_name=$(bluer_ai_option "$options" name bluer_ai)

    local exists=$(bluer_ai_conda_exists name=$environment_name)
    if [[ "$exists" == 0 ]]; then
        bluer_ai_log_warning "@conda: $environment_name does not exist."
        return 0
    fi

    conda activate base
    [[ $? -ne 0 ]] && return 1

    bluer_ai_eval ,$options \
        conda remove -y \
        --name $environment_name \
        --all
}
