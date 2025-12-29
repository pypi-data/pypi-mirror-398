#! /usr/bin/env bash

function bluer_ai_terraform_get() {
    if [[ "$abcli_is_mac" == true ]]; then
        echo ~/.bash_profile
        return
    fi

    if [[ "$abcli_is_rpi" == true ]]; then
        echo "/home/pi/.bashrc"
        return
    fi

    if [[ "$abcli_is_ubuntu" == true ]]; then
        if [[ "$abcli_is_ec2" == true ]]; then
            echo "/home/$USER/.bash_profile"
        else
            echo "/home/$USER/.bashrc"
        fi
        return
    fi

    echo "unknown"
}
