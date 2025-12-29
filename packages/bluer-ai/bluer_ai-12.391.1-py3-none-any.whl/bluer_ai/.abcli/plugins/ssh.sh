#! /usr/bin/env bash

function bluer_ai_add_ssh_keys() {
    if [ -z "$BLUER_AI_SSH_KEYS_ADDED" ] || [ "$1" == "force" ]; then
        eval "$(ssh-agent -s)"

        ssh-add -k $HOME/.ssh/$BLUER_AI_GIT_SSH_KEY_NAME

        if [ -f "$HOME/.ssh/abcli" ]; then
            ssh-add -k $HOME/.ssh/abcli
        fi

        export BLUER_AI_SSH_KEYS_ADDED="true"
    fi
}

function bluer_ai_ssh() {
    local task=$1

    if [ "$task" == "add" ]; then
        local filename=$(bluer_ai_clarify_input $2 abcli)

        ssh-add -k $HOME/.ssh/$filename
        return
    fi

    # https://www.raspberrypi.com/tutorials/cluster-raspberry-pi-tutorial/
    if [ "$task" == "copy_id" ]; then
        local filename=$(bluer_ai_clarify_input $2 abcli)
        local args=$(bluer_ai_ssh_args "${@:3}")

        ssh-copy-id -i $HOME/.ssh/$filename.pub $args
        return
    fi

    # https://www.raspberrypi.com/tutorials/cluster-raspberry-pi-tutorial/
    if [ "$task" == "keygen" ]; then
        local filename=$(bluer_ai_clarify_input $2 abcli)
        ssh-keygen -t rsa -b 4096 -f $HOME/.ssh/$filename
        return
    fi

    local args=$(bluer_ai_ssh_args "$@")
    bluer_ai_log "@ssh: $args"
    ssh $args
}

function bluer_ai_ssh_args() {
    local machine_kind=$(bluer_ai_clarify_input $1 local)
    local machine_name=$2
    local options=$3
    local copy_seed=$(bluer_ai_option_int "$options" seed 1)
    local for_vnc=$(bluer_ai_option_int "$options" vnc 0)

    if [ "$machine_kind" == "ec2" ]; then
        local address=$(echo "$machine_name" | tr . -)
        local region=$(bluer_ai_option "$options" region $ABCLI_AWS_REGION)
        local url="ec2-$address.$region.compute.amazonaws.com"
        local user=$(bluer_ai_option "$options" user ubuntu)

        ssh-keyscan $url >>~/.ssh/known_hosts

        local address="$user@$url"

        if [ "$copy_seed" == 1 ]; then
            bluer_ai_seed ec2 clipboard,env=worker,~log
        fi

        local pem_filename=$ABCLI_PATH_IGNORE/$abcli_aws_ec2_key_name.pem
        chmod 400 $pem_filename
        if [ "$for_vnc" == 1 ]; then
            echo "-i $pem_filename -L 5901:localhost:5901 $address"
        else
            echo "-i $pem_filename $address"
        fi
        return
    fi

    if [ "$machine_kind" == "jetson_nano" ]; then
        echo abcli@$machine_name.local
        return
    fi

    if [ "$machine_kind" == "local" ]; then
        echo ""
        return
    fi

    if [ "$machine_kind" == "rpi" ]; then
        echo pi@$machine_name.local
        return
    fi

    echo "unknown"
    bluer_ai_log_error "bluer_ai_ssh_args: $machine_kind: machine kind not found."
}
