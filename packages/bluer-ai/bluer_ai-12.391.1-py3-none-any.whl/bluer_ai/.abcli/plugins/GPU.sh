#! /usr/bin/env bash

function bluer_ai_gpu() {
    local task=${1:-status}

    local function_name=bluer_ai_gpu_$task
    if [[ $(type -t $function_name) == "function" ]]; then
        $function_name "${@:2}"
        return
    fi

    if [ $task == "validate" ]; then
        bluer_ai_log $(python3 -m bluer_ai.plugins.gpu validate)
        return
    fi

    bluer_ai_log_error "@gpu: $task: command not found."
    return 1
}

function bluer_ai_gpu_status() {
    local task=${1:-show}

    if [ $task == "get" ]; then
        local options=$2
        local from_cache=$(bluer_ai_option_int "$options" from_cache 1)

        local status=""
        [[ "$from_cache" == 1 ]] &&
            local status=$bluer_ai_gpu_status_cache

        [[ -z "$status" ]] &&
            local status=$(python3 -m bluer_ai.plugins.gpu \
                status \
                "${@:3}")

        export bluer_ai_gpu_status_cache=$status

        $bluer_ai_gpu_status_cache && local message="found. ✅" || local message='not found.'
        bluer_ai_log "🔋 gpu: $message"
        return
    fi

    if [ $task == "show" ]; then
        bluer_ai_eval - nvidia-smi

        bluer_ai_log "CUDA_VISIBLE_DEVICES=$CUDA_VISIBLE_DEVICES"

        bluer_ai_gpu_status get

        bluer_ai_gpu validate

        return
    fi

    bluer_ai_log_error "@gpu: status: $task: command not found."
    return 1
}

bluer_ai_gpu_status get
$bluer_ai_gpu_status_cache && export abcli_status_icons="🔋 $abcli_status_icons"
