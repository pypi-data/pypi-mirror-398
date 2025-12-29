#! /usr/bin/env bash

function test_bluer_ai_option() {
    local options=$1

    options="a,~b,c=1,d=0,var_e,-f,g=2,h=that"

    bluer_ai_assert $(bluer_ai_option "$options" a) True
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert $(bluer_ai_option "$options" a default) True
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert $(bluer_ai_option "$options" b) False
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert $(bluer_ai_option "$options" b default) False
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert $(bluer_ai_option "$options" c) 1
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert $(bluer_ai_option "$options" c default) 1
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert $(bluer_ai_option "$options" d) 0
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert $(bluer_ai_option "$options" d default) 0
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert $(bluer_ai_option "$options" var_e) True
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert $(bluer_ai_option "$options" var_e default) True
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert $(bluer_ai_option "$options" f) False
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert $(bluer_ai_option "$options" f default) False
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert $(bluer_ai_option "$options" g) 2
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert $(bluer_ai_option "$options" g default) 2
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert $(bluer_ai_option "$options" h) that
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert $(bluer_ai_option "$options" h default) that
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert $(bluer_ai_option "$options" other) ""
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert $(bluer_ai_option "$options" other default) default
}

function test_bluer_ai_option_choice() {
    local options=$1

    bluer_ai_assert \
        $(bluer_ai_option_choice \
            "x=1,~y,separated,z=12" comma,separated,list default) separated
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert \
        $(bluer_ai_option_choice \
            "x=1,~y,separated,z=12" comma,separated,list) separated
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert \
        $(bluer_ai_option_choice \
            "x=1,~y,attached,z=12" comma,separated,list default) default
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert \
        $(bluer_ai_option_choice \
            "x=1,~y,attached,z=12" comma,separated,list) ""
}

function test_bluer_ai_option_int() {
    local options=$1

    options="a,~b,c=1,d=0,var_e,-f"

    bluer_ai_assert $(bluer_ai_option_int "$options" a) 1
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert $(bluer_ai_option_int "$options" a 0) 1
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert $(bluer_ai_option_int "$options" a 1) 1
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert $(bluer_ai_option_int "$options" b) 0
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert $(bluer_ai_option_int "$options" b 0) 0
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert $(bluer_ai_option_int "$options" b 1) 0
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert $(bluer_ai_option_int "$options" c) 1
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert $(bluer_ai_option_int "$options" c 0) 1
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert $(bluer_ai_option_int "$options" c 1) 1
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert $(bluer_ai_option_int "$options" d) 0
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert $(bluer_ai_option_int "$options" d 0) 0
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert $(bluer_ai_option_int "$options" d 1) 0
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert $(bluer_ai_option_int "$options" var_e) 1
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert $(bluer_ai_option_int "$options" var_e 0) 1
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert $(bluer_ai_option_int "$options" var_e 1) 1
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert $(bluer_ai_option_int "$options" f) 0
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert $(bluer_ai_option_int "$options" f 0) 0
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert $(bluer_ai_option_int "$options" f 1) 0
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert $(bluer_ai_option_int "$options" g) 0
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert $(bluer_ai_option_int "$options" g 0) 0
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert $(bluer_ai_option_int "$options" g 1) 1
}
