#! /usr/bin/env bash

function test_bluer_ai_repeat() {
    bluer_ai_repeat - ls
    bluer_ai_assert "$?" 0
    [[ $? -ne 0 ]] && return 1

    bluer_ai_repeat count=3 ls
    bluer_ai_assert "$?" 0
}
