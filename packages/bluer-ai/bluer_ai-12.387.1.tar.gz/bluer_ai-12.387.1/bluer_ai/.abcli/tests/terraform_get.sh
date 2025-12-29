#! /usr/bin/env bash

function test_bluer_ai_terraform_get() {
    local options=$1

    bluer_ai_eval ,$options \
        bluer_ai \
        terraform \
        get \
        "${@:2}"

    return 0
}
