#! /usr/bin/env bash

function bluer_ai_conda_list() {
    bluer_ai_eval ,$1 \
        conda info \
        --envs "${@:2}"
}
