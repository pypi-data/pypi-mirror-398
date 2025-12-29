#! /usr/bin/env bash

export abcli_status_icons=""

export abcli_path_bash="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"

function bluer_ai_main() {
    echo -e "\033]1337;SetBadgeFormat=$(echo -n "🌀" | base64)\a"

    local options=$1

    if [[ ",$options," == *",verbose,"* ]]; then
        set -x
        touch $abcli_path_bash/../../verbose
    fi

    export abcli_is_silent=false
    [[ ",$options," == *",silent,"* ]] && export abcli_is_silent=true

    export abcli_is_in_notebook=false
    [[ ",$options," == *",in_notebook,"* ]] && export abcli_is_in_notebook=true

    export abcli_is_aws_batch=false
    [[ ",$options," == *",aws_batch,"* ]] && export abcli_is_aws_batch=true

    export abcli_is_colorful=true
    [[ "$abcli_is_aws_batch" == true ]] || [[ "$abcli_is_silent" == true ]] ||
        [[ ",$options," == *",mono,"* ]] &&
        export abcli_is_colorful=false

    source $abcli_path_bash/bootstrap/dependencies.sh
    bluer_ai_source_dependencies

    local do_terraform=1
    [[ "$abcli_is_mac" == true ]] && do_terraform=0
    do_terraform=$(bluer_ai_option_int "$options" terraform $do_terraform)

    [[ "$do_terraform" == 1 ]] &&
        bluer_ai_terraform

    bluer_ai_initialize

    [[ "$abcli_is_in_notebook" == false ]] &&
        bluer_ai_select $abcli_object_name

    local where=$(bluer_ai_option "$options" where)
    bluer_ai_log "🌀 $abcli_fullname $where"

    local return_if_not_ssh=$(bluer_ai_option_int "$options" if_not_ssh 0)
    if [[ "$return_if_not_ssh" == 1 ]] && [[ "$abcli_is_ssh_session" == true ]]; then
        bluer_ai_log "ssh session detected."
        return 0
    fi

    local command_line="${@:2}"
    if [[ ! -z "$command_line" ]]; then
        bluer_ai_eval - "$command_line"
        if [[ $? -ne 0 ]]; then
            bluer_ai_log_error "@main: failed: $command_line"
            return 1
        else
            bluer_ai_log "✅ $command_line"
            return 0
        fi
    fi
}

if [ -f "$HOME/storage/temp/ignore/disabled" ]; then
    printf "bluer-ai is \033[0;31mdisabled\033[0m, run '@terraform enable' first.\n"
else
    bluer_ai_main "$@"
fi
