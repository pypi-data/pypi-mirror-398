#! /usr/bin/env bash

function test_bluer_ai_assert() {
    bluer_ai_assert x x
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert x x yes
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert x x no
    [[ $? -eq 0 ]] && return 1

    bluer_ai_assert x y
    [[ $? -eq 0 ]] && return 1

    bluer_ai_assert x y yes
    [[ $? -eq 0 ]] && return 1

    bluer_ai_assert x y no
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert "" - yes
    [[ $? -eq 0 ]] && return 1

    bluer_ai_assert "" - no
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert "" - non-empty
    [[ $? -eq 0 ]] && return 1

    bluer_ai_assert x - non-empty
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert "" - empty
}

function test_bluer_ai_assert_file_exists() {
    local path=$(python3 -m bluer_options locate)

    bluer_ai_assert_file_exists \
        $path/void.py
    [[ $? -eq 0 ]] && return 1

    bluer_ai_assert_file_exists \
        $path/__init__.py
}

function test_bluer_ai_assert_list() {
    bluer_ai_assert_list \
        this,that,who,what \
        which,that,this,what
    [[ $? -eq 0 ]] && return 1

    bluer_ai_assert_list \
        this,that,which,what \
        which,that,this,what
}
