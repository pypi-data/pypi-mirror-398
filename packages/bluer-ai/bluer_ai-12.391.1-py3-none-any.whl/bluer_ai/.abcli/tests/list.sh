#! /usr/bin/env bash

function test_bluer_ai_list_filter() {
    bluer_ai_assert \
        $(bluer_ai_list_filter this,which,that,who,12 \
            --contains th) \
        this,that
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert \
        $(bluer_ai_list_filter this,which,that,who,12 \
            --doesnt_contain wh) \
        this,that,12
}

function test_bluer_ai_list_in() {
    bluer_ai_assert \
        $(bluer_ai_list_in that this,that,which) \
        True
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert \
        $(bluer_ai_list_in who this,that,which) \
        False
}

function test_bluer_ai_list_intersect() {
    bluer_ai_assert_list \
        $(bluer_ai_list_intersect this,that,who which,that,what,this) \
        this,that
}

function test_bluer_ai_list_item() {
    bluer_ai_assert \
        $(bluer_ai_list_item this,that,who 1) \
        that
}

function test_bluer_ai_list_len() {
    bluer_ai_assert \
        $(bluer_ai_list_len this,that,which) \
        3
}

function test_bluer_ai_list_nonempty() {
    bluer_ai_assert \
        $(bluer_ai_list_nonempty this,,that) \
        this,that
}

function test_bluer_ai_list_next() {
    bluer_ai_assert \
        $(bluer_ai_list_next what what,which,this,that,something) \
        which
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert \
        $(bluer_ai_list_next this what,which,this,that,something) \
        that
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert \
        "$(bluer_ai_list_next something what,which,this,that,something)" \
        - empty
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert \
        "$(bluer_ai_list_next void what,which,this,that,something)" \
        - empty
}

function test_bluer_ai_list_prev() {
    bluer_ai_assert \
        "$(bluer_ai_list_prev what what,which,this,that,something)" \
        - empty
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert \
        $(bluer_ai_list_prev this what,which,this,that,something) \
        which
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert \
        $(bluer_ai_list_prev something what,which,this,that,something) \
        that
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert \
        "$(bluer_ai_list_prev void what,which,this,that,something)" \
        - empty
}

function test_bluer_ai_list_resize() {
    bluer_ai_assert \
        $(bluer_ai_list_resize this,that,which 2) \
        this,that
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert \
        $(bluer_ai_list_resize this,that,which -1) \
        this,that,which
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert \
        "$(bluer_ai_list_resize this,that,which 0)" \
        - empty
}

function test_bluer_ai_list_reverse() {
    bluer_ai_assert \
        $(bluer_ai_list_reverse this,that,which) \
        which,that,this
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert \
        $(bluer_ai_list_reverse this) \
        this
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert \
        "$(bluer_ai_list_reverse)" \
        - empty
}

function test_bluer_ai_list_sort() {
    bluer_ai_assert \
        $(bluer_ai_list_sort this,that) \
        that,this
    [[ $? -ne 0 ]] && return 1

    bluer_ai_assert \
        $(bluer_ai_list_sort this,that,this,12,which \
            --unique 1) \
        12,that,this,which
}
