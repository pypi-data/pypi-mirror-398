#! /usr/bin/env bash

function bluer_ai_log() {
    local task=$1

    if [[ "$task" == "rm" ]]; then
        rm -v $bluer_ai_log_filename
        return
    fi

    if [[ "$task" == "verbose" ]]; then
        local what=${2:-on}

        if [ "$what" == "on" ]; then
            touch $abcli_path_git/verbose
            bluer_ai_set_log_verbosity
        elif [ "$what" == "off" ]; then
            rm $abcli_path_git/verbose
            bluer_ai_set_log_verbosity
        else
            bluer_ai_log_error "@log: verbose: $what: command not found."
            return 1
        fi

        return
    fi

    if [[ "$task" == "watch" ]]; then
        local options=$2
        local rpi=$(bluer_ai_option_int "$options" rpi 0)

        if [[ "$rpi" == 1 ]]; then
            local machine_name=$3
            if [[ -z "$machine_name" ]]; then
                bluer_ai_log_error "machine_name not found."
                return 1
            fi

            bluer_ai_badge "$machine_name"

            ssh \
                pi@$machine_name.local \
                "tail -f /home/pi/git/bluer_ai.log"

            bluer_ai_badge "🌀"
            return
        fi

        tail -f $bluer_ai_log_filename "${@:2}"
        return
    fi

    bluer_ai_log_local "$@"

    bluer_ai_log_remote "$@"
}

function bluer_ai_log_error() {
    local message="$@"

    printf "❗️ ${RED}$message$NC\n"

    echo "error: $message" >>$bluer_ai_log_filename
}

function bluer_ai_log_remote() {
    echo "$@" >>$bluer_ai_log_filename
}

function bluer_ai_log_warning() {
    local message="$@"

    printf "$YELLOW$message$NC\n"

    echo "warning: $message" >>$bluer_ai_log_filename
}

function bluer_ai_set_log_verbosity() {
    if [[ -f $abcli_path_git/verbose ]]; then
        set -x
    else
        set +x
    fi
}

bluer_ai_set_log_verbosity

if [ -z "$bluer_ai_log_filename" ]; then
    export bluer_ai_log_filename=$abcli_path_git/bluer_ai.log
fi
