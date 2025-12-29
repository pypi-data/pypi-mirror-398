#! /usr/bin/env bash

function test_bluer_ai_README() {
    local options=$1

    bluer_ai_eval ,$options \
        bluer_ai build_README
}
