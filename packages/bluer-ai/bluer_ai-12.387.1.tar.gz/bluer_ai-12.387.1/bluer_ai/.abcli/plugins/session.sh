#! /usr/bin/env bash

function bluer_ai_session() {
    local task=${1:-start}

    if [ $task == "start" ]; then
        local options=$2

        local do_pull=1
        [[ "$abcli_is_mac" == true ]] && do_pull=0
        do_pull=$(bluer_ai_option_int "$options" pull $do_pull)

        bluer_ai_log "session started: $options ${@:3}"

        while true; do
            [[ "$do_pull" == 1 ]] &&
                bluer_ai_git_pull init

            bluer_ai_log "session initialized: username=$USER, hostname=$(hostname), EUID=$EUID, python3=$(which python3)"

            local sudo_prefix=""
            [[ "$BLUER_AI_SESSION_IS_SUDO" == 1 ]] &&
                sudo_prefix="sudo"

            $sudo_prefix \
                rm -v $ABCLI_PATH_IGNORE/session_reply_*

            [[ "$abcli_is_mac" == false ]] &&
                bluer_ai_storage clear

            local plugin_name=$(bluer_ai_option "$options" plugin $BLUER_SBC_SESSION_PLUGIN)
            local function_name=${plugin_name}_session
            if [[ $(type -t $function_name) == "function" ]]; then
                $function_name start "${@:3}"
            else
                if [ -z "$plugin_name" ]; then
                    bluer_ai_log_warning "@session: plugin not found."
                else
                    bluer_ai_log_error "@session: plugin: $plugin_name: $function_name: session function not found."
                fi
                bluer_ai_sleep seconds=60
            fi

            bluer_ai_log "session closed."

            if [ -f "$ABCLI_PATH_IGNORE/session_reply_exit" ]; then
                bluer_ai_log "reply_to_bash(exit)"
                return
            fi

            if [ -f "$ABCLI_PATH_IGNORE/session_reply_reboot" ]; then
                bluer_ai_log "reply_to_bash(reboot)"
                bluer_objects_host reboot
            fi

            if [ -f "$ABCLI_PATH_IGNORE/session_reply_seed" ]; then
                bluer_ai_log "reply_to_bash(seed)"

                bluer_ai_git_pull
                bluer_ai_init

                cat "$ABCLI_PATH_IGNORE/session_reply_seed" | while read line; do
                    bluer_ai_log "executing: $line"
                    eval $line
                done
            fi

            if [ -f "$ABCLI_PATH_IGNORE/session_reply_shutdown" ]; then
                bluer_objects_host shutdown
            fi

            if [ -f "$ABCLI_PATH_IGNORE/session_reply_update" ]; then
                bluer_ai_log "reply_to_bash(update)"
            fi

            if [ -f "$ABCLI_PATH_IGNORE/disabled" ]; then
                bluer_ai_log "bluer_ai is disabled."
                return
            fi

            bluer_ai_sleep seconds=5
        done

        return
    fi

    bluer_ai_log_error "@session: $task: command not found."
    return 1
}
