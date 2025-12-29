#! /usr/bin/env bash

function test_bluer_ai_eval() {
    bluer_ai_eval - ls
    bluer_ai_assert "$?" 0
    [[ $? -ne 0 ]] && return 1

    bluer_ai_eval - lsz
    bluer_ai_assert "$?" 0 not
}
