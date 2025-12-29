#! /usr/bin/env bash

function test_bluer_ai_clarify_object_no_default() {
    local object_1=$(bluer_ai_string_timestamp)
    local object_2=$(bluer_ai_string_timestamp)
    local object_3=$(bluer_ai_string_timestamp)

    local var

    bluer_ai_select $object_3
    bluer_ai_select $object_2
    bluer_ai_select $object_1

    bluer_ai_assert \
        $(bluer_ai_clarify_object some-value) \
        some-value
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert \
        $(bluer_ai_clarify_object -) \
        - non-empty
    [[ $? -ne 0 ]] && return 1

    var=""
    bluer_ai_assert \
        $(bluer_ai_clarify_object $var) \
        - non-empty
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert \
        $(bluer_ai_clarify_object .) \
        $object_1
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert \
        $(bluer_ai_clarify_object ..) \
        $object_2
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert \
        $(bluer_ai_clarify_object ...) \
        $object_3
}

function test_bluer_ai_clarify_object_some_default() {
    local object_1=$(bluer_ai_string_timestamp)
    local object_2=$(bluer_ai_string_timestamp)
    local object_3=$(bluer_ai_string_timestamp)

    local var

    bluer_ai_select $object_3
    bluer_ai_select $object_2
    bluer_ai_select $object_1

    bluer_ai_assert \
        $(bluer_ai_clarify_object some-value some-default) \
        some-value
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert \
        $(bluer_ai_clarify_object - some-default) \
        some-default
    [[ $? -ne 0 ]] && return 1

    var=""
    bluer_ai_assert \
        $(bluer_ai_clarify_object $var some-default) \
        some-default
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert \
        $(bluer_ai_clarify_object . some-default) \
        $object_1
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert \
        $(bluer_ai_clarify_object .. some-default) \
        $object_2
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert \
        $(bluer_ai_clarify_object ... some-default) \
        $object_3
}

function test_bluer_ai_clarify_object_dot_default() {
    local object_1=$(bluer_ai_string_timestamp)
    local object_2=$(bluer_ai_string_timestamp)
    local object_3=$(bluer_ai_string_timestamp)

    local var

    bluer_ai_select $object_3
    bluer_ai_select $object_2
    bluer_ai_select $object_1

    bluer_ai_assert \
        $(bluer_ai_clarify_object some-value .) \
        some-value
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert \
        $(bluer_ai_clarify_object - .) \
        $object_1
    [[ $? -ne 0 ]] && return 1

    var=""
    bluer_ai_assert \
        $(bluer_ai_clarify_object $var .) \
        $object_1
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert \
        $(bluer_ai_clarify_object . .) \
        $object_1
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert \
        $(bluer_ai_clarify_object .. .) \
        $object_2
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert \
        $(bluer_ai_clarify_object ... .) \
        $object_3
}

function test_bluer_ai_clarify_object_dot_dot_default() {
    local object_1=$(bluer_ai_string_timestamp)
    local object_2=$(bluer_ai_string_timestamp)
    local object_3=$(bluer_ai_string_timestamp)

    local var

    bluer_ai_select $object_3
    bluer_ai_select $object_2
    bluer_ai_select $object_1

    bluer_ai_assert \
        $(bluer_ai_clarify_object some-value ..) \
        some-value
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert \
        $(bluer_ai_clarify_object - ..) \
        $object_2
    [[ $? -ne 0 ]] && return 1

    var=""
    bluer_ai_assert \
        $(bluer_ai_clarify_object $var ..) \
        $object_2
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert \
        $(bluer_ai_clarify_object . ..) \
        $object_1
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert \
        $(bluer_ai_clarify_object .. ..) \
        $object_2
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert \
        $(bluer_ai_clarify_object ... ..) \
        $object_3
}

function test_bluer_ai_clarify_object_dot_dot_dot_default() {
    local object_1=$(bluer_ai_string_timestamp)
    local object_2=$(bluer_ai_string_timestamp)
    local object_3=$(bluer_ai_string_timestamp)

    local var

    bluer_ai_select $object_3
    bluer_ai_select $object_2
    bluer_ai_select $object_1

    bluer_ai_assert \
        $(bluer_ai_clarify_object some-value ...) \
        some-value
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert \
        $(bluer_ai_clarify_object - ...) \
        $object_3
    [[ $? -ne 0 ]] && return 1

    var=""
    bluer_ai_assert \
        $(bluer_ai_clarify_object $var ...) \
        $object_3
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert \
        $(bluer_ai_clarify_object . ...) \
        $object_1
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert \
        $(bluer_ai_clarify_object .. ...) \
        $object_2
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert \
        $(bluer_ai_clarify_object ... ...) \
        $object_3
}
