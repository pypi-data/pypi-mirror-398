#! /usr/bin/env bash

function test_bluer_ai_clarify_input() {
    bluer_ai_assert \
        $(bluer_ai_clarify_input - default-value) \
        default-value
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert \
        $(bluer_ai_clarify_input "" default-value) \
        default-value
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert \
        $(bluer_ai_clarify_input value default-value) \
        value
}
