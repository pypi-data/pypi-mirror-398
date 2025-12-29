#! /usr/bin/env bash

function test_bluer_ai_env() {
    bluer_ai_env
    [[ $? -ne 0 ]] && return 1

    bluer_ai_env path
    [[ $? -ne 0 ]] && return 1

    bluer_ai_env_dot_cat config
    [[ $? -ne 0 ]] && return 1

    bluer_ai_env_dot_cat
    [[ $? -ne 0 ]] && return 1

    bluer_ai_env_dot_cat nurah
    [[ $? -ne 0 ]] && return 1

    bluer_ai_env_dot get TBD
    [[ $? -ne 0 ]] && return 1

    bluer_ai_env_dot list
    [[ $? -ne 0 ]] && return 1

    bluer_ai_env_dot_seed \
        $(python3 -m bluer_ai locate)
}
