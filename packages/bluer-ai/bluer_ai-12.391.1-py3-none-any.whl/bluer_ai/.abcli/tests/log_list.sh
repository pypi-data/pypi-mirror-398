#! /usr/bin/env bash

function test_bluer_ai_log_list() {
    bluer_ai_log_list this+that \
        --before "list of" \
        --delim + \
        --after "important thing(s)"
    [[ $? -ne 0 ]] && return 1

    bluer_ai_log_list "this that" \
        --before "list of" \
        --delim space \
        --after "important thing(s)"
    [[ $? -ne 0 ]] && return 1

    bluer_ai_log_list "this,that" \
        --before "list of" \
        --delim , \
        --after "important thing(s)"
    [[ $? -ne 0 ]] && return 1

    bluer_ai_log_list "this,that" \
        --before "list of" \
        --delim , \
        --after "important thing(s)" \
        --sorted 1
    [[ $? -ne 0 ]] && return 1

    bluer_ai_log_list this,that
}
