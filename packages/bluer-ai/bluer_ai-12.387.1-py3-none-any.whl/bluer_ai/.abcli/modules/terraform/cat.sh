#! /usr/bin/env bash

function bluer_ai_terraform_cat() {
    if [[ "$abcli_is_mac" == true ]]; then
        bluer_ai_log_local_and_cat ~/.bash_profile
        return
    fi

    if [[ "$abcli_is_rpi" == true ]]; then
        bluer_ai_log_local_and_cat "/home/pi/.bashrc"

        if [[ "$abcli_is_headless" == false ]]; then
            if [[ "$abcli_is_rpi4" == true ]]; then
                bluer_ai_log_local_and_cat /etc/systemd/system/bluer_ai.service
            else
                bluer_ai_log_local_and_cat /etc/xdg/lxsession/LXDE-pi/autostart
            fi
        fi
        return
    fi

    if [[ "$abcli_is_ubuntu" == true ]]; then
        if [[ "$abcli_is_ec2" == true ]]; then
            bluer_ai_log_local_and_cat "/home/$USER/.bash_profile"
        else
            bluer_ai_log_local_and_cat "/home/$USER/.bashrc"

            if [[ "$abcli_is_jetson" == true ]]; then
                bluer_ai_log_local_and_cat "/home/$USER/.config/autostart/abcli.desktop"
            fi
        fi
        return
    fi
}
