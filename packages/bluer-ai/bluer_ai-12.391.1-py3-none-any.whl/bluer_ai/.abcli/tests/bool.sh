#! /usr/bin/env bash

function test_bluer_ai_not() {
    bluer_ai_assert \
        $(bluer_ai_not 1) \
        0
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert \
        $(bluer_ai_not 0) \
        1
}
