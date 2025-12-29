#! /usr/bin/env bash

export abcli_is_64bit=false
export abcli_is_amazon_linux=false
export abcli_is_cloudshell=false
export abcli_is_docker=false
export abcli_is_ec2=false
export abcli_is_github_workflow=false
export abcli_is_jetson=false
export abcli_is_headless=false
export abcli_is_mac=false
export abcli_is_rpi=false
export abcli_is_rpi4=false
export abcli_is_rpi5=false
export abcli_is_sagemaker=false
export abcli_is_sagemaker_system=false
export abcli_is_ssh_session=false
export abcli_is_ubuntu=false
export abcli_is_vnc=false

if [[ -n "$SSH_CONNECTION" ]]; then
    export abcli_is_ssh_session=true
fi

# https://github.com/ultralytics/yolov5/blob/master/utils/general.py#L90
# https://stackoverflow.com/a/25518538/17619982
if [ -f "/.dockerenv" ]; then
    export abcli_is_docker=true

    # https://stackoverflow.com/a/38983893/17619982
    export abcli_container_id=$(cat /etc/hostname)

    alias sudo=
    alias dmidecode=true
fi

if [[ "|x86_64|aarch64|" == *"|$(uname -m)|"* ]]; then
    export abcli_is_64bit=true
fi

if [ -f "$ABCLI_PATH_IGNORE/headless" ]; then
    export abcli_is_headless=true
fi

if [ -f "$abcli_path_git/vnc" ]; then
    export abcli_is_vnc=true
fi

if [[ "$OSTYPE" == "darwin"* ]]; then
    export abcli_is_mac=true
fi

if [[ "$HOME" == "/home/sagemaker-user" ]]; then
    export abcli_is_sagemaker=true
    export abcli_is_sagemaker_system=true
elif [[ "$HOME" == "/home/cloudshell-user" ]]; then
    export abcli_is_cloudshell=true
elif [[ "$(hostname)" == sagemaker* ]] || [[ "$(hostname)" == pytorch* ]]; then
    export abcli_is_sagemaker=true
fi

if [[ "$OSTYPE" == "linux-gnueabihf" ]]; then
    export abcli_is_rpi=true
fi

if [[ "$GITHUB_ACTIONS" == true ]]; then
    export abcli_is_github_workflow=true
fi

if [[ "$OSTYPE" == "linux-gnu" ]]; then
    export abcli_is_ubuntu=true

    if [[ "$abcli_is_docker" == false ]] && [[ "$abcli_is_aws_batch" == false ]]; then
        export abcli_hardware_model=$(tr -d '\0' </proc/device-tree/model 2>/dev/null)
        if [[ "$abcli_hardware_model" == *"Raspberry Pi"* ]]; then
            export abcli_is_rpi=true
            export abcli_is_ubuntu=false

            [[ "$abcli_hardware_model" == *"Raspberry Pi 4"* ]] &&
                export abcli_is_rpi4=true

            [[ "$abcli_hardware_model" == *"Raspberry Pi 5"* ]] &&
                export abcli_is_rpi5=true

        elif [[ "$abcli_is_64bit" == false ]]; then
            export abcli_is_jetson=true
            # https://forums.developer.nvidia.com/t/read-serial-number-of-jetson-nano/72955
            export abcli_jetson_nano_serial_number=$(sudo cat /proc/device-tree/serial-number)

            # https://github.com/numpy/numpy/issues/18131#issuecomment-755438271
            # https://github.com/numpy/numpy/issues/18131#issuecomment-756140369
            export OPENBLAS_CORETYPE=ARMV8
        elif [[ "$(sudo dmidecode -s bios-version)" == *"amazon" ]] || [[ "$(sudo dmidecode -s bios-vendor)" == "Amazon"* ]]; then
            export abcli_is_ec2=true

            if [[ "$USER" == "ec2-user" ]]; then
                export abcli_is_amazon_linux=true
                # https://unix.stackexchange.com/a/191125
                export abcli_ec2_instance_id=$(ec2-metadata --instance-id | cut -d' ' -f2)
            else
                export abcli_ec2_instance_id=$(ec2metadata --instance-id)
            fi
        else
            # https://stackoverflow.com/a/22991546
            export abcli_ubuntu_computer_id=$(sudo dmidecode | grep -w UUID | sed "s/^.UUID\: //g")
        fi
    fi
fi

function bluer_ai_announce() {
    local status=""

    [[ "$abcli_is_64bit" == true ]] &&
        status="$status 64-bit"
    [[ "$abcli_is_amazon_linux" == true ]] &&
        status="$status amazon-linux"
    [[ "$abcli_is_cloudshell" == true ]] &&
        status="$status cloudshell"
    [[ "$abcli_is_docker" == true ]] &&
        status="$status docker"
    [[ "$abcli_is_ec2" == true ]] &&
        status="$status ec2"
    [[ "$abcli_is_github_workflow" == true ]] &&
        status="$status github-workflow"
    [[ "$abcli_is_jetson" == true ]] &&
        status="$status jetson"
    [[ "$abcli_is_headless" == true ]] &&
        status="$status headless"
    [[ "$abcli_is_mac" == true ]] &&
        status="$status mac"
    [[ "$abcli_is_rpi" == true ]] &&
        status="$status rpi"
    [[ "$abcli_is_sagemaker" == true ]] &&
        status="$status sagemaker"
    [[ "$abcli_is_sagemaker_system" == true ]] &&
        status="$status sagemaker-system"
    [[ "$abcli_is_ssh_session" == true ]] &&
        status="$status ssh-session"
    [[ "$abcli_is_ubuntu" == true ]] &&
        status="$status ubuntu"
    [[ "$abcli_is_vnc" == true ]] &&
        status="$status vnc"

    status="$status @ $OSTYPE"
    [[ ! -z "$abcli_hardware_model" ]] &&
        status="$status on $abcli_hardware_model"

    echo "🌀$status"
}
bluer_ai_announce

export abcli_base64="base64"
# https://superuser.com/a/1225139
[[ "$abcli_is_ubuntu" == true ]] && export abcli_base64="base64 -w 0"

if [[ "$abcli_is_ec2" == true ]]; then
    source $HOME/.bashrc
    # https://stackoverflow.com/a/17723894/17619982
    # export LD_PRELOAD=/usr/lib/arm-linux-gnueabihf/libatomic.so.1
fi

if [[ "$abcli_is_rpi" == true ]]; then
    if [[ "$abcli_is_headless" == false ]]; then
        # https://www.geeks3d.com/hacklab/20160108/how-to-disable-the-blank-screen-on-raspberry-pi-raspbian/
        sudo xset s off
        sudo xset -dpms
        sudo xset s noblank

        # wait for internet connection to establish
        sleep 5
    fi
fi

if [[ "$abcli_is_sagemaker_system" == true ]]; then
    export abcli_hostname=sagemaker_system
elif [[ "$abcli_is_cloudshell" == true ]]; then
    export abcli_hostname=cloudshell
else
    export abcli_hostname=$(hostname)
fi
echo "🌀 host: $abcli_hostname"

function bluer_ai_kill_all() {
    # if [[ "$abcli_is_sagemaker" == true ]] || [[ "$abcli_is_cloudshell" == true ]]; then
    if [[ "$abcli_is_docker" == true ]] || [[ "$abcli_is_aws_batch" == true ]]; then
        # https://unstop.com/blog/kill-process-linux
        pkill "$@"
    else
        # https://unix.stackexchange.com/a/94528
        sudo killall "$@"
    fi
}
