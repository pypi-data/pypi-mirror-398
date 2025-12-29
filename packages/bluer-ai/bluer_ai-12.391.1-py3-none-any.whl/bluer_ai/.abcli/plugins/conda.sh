#! /usr/bin/env bash

function bluer_ai_conda() {
    local task=$1

    local function_name="bluer_ai_conda_$task"
    if [[ $(type -t $function_name) == "function" ]]; then
        $function_name "${@:2}"
        return
    fi

    conda "$@"
}

bluer_ai_source_caller_suffix_path /conda
