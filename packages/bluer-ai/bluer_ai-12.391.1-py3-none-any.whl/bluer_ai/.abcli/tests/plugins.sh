#! /usr/bin/env bash

function test_bluer_ai_plugin_name_from_repo() {
    local options=$1

    bluer_ai_assert \
        $(bluer_ai_plugin_name_from_repo bluer-ai) \
        bluer_ai
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert \
        $(bluer_ai_plugin_name_from_repo blueness) \
        blueness
}

function test_bluer_ai_get_module_name_from_plugin() {
    bluer_ai_assert \
        $(bluer_ai_get_module_name_from_plugin bluer_ai) \
        bluer_ai
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert \
        $(bluer_ai_get_module_name_from_plugin blueness) \
        blueness
}
