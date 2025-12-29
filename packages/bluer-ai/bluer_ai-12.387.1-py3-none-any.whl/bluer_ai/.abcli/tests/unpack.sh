#! /usr/bin/env bash

function test_bluer_ai_unpack_repo_name() {
    bluer_ai_assert \
        $(bluer_ai_unpack_repo_name bluer-ai) \
        bluer-ai
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert \
        $(bluer_ai_unpack_repo_name bluer_ai) \
        bluer-ai
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert \
        $(bluer_ai_unpack_repo_name @ai) \
        bluer-ai
}
