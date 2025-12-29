#! /usr/bin/env bash

function bluer_ai_clarify_input() {
    local default=$2
    local value=${1:-$default}

    [[ "$value" == "-" ]] &&
        value=$default

    echo $value
}
