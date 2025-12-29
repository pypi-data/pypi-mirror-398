#! /usr/bin/env bash

function bluer_ai_conda_exists() {
    local options=$1
    local environment_name=$(bluer_ai_option "$options" name bluer_ai)

    if conda info --envs | grep -q "^$environment_name "; then
        echo 1
    else
        echo 0
    fi
}
