#! /usr/bin/env bash

function bluer_ai_wifi_get_ssid() {
    if [ "$abcli_is_jetson" == true ] || [ "$abcli_is_rpi" == true ]; then
        # https://code.luasoftware.com/tutorials/jetson-nano/jetson-nano-connect-to-wifi-via-command-line/
        # https://howchoo.com/pi/find-raspberry-pi-network-name-ssid
        local temp=$(iwgetid)
        python3 -c "print('$temp'.split('\"')[1] if '\"' in '$temp' else 'offline')"
    elif [ "$abcli_is_mac" == true ]; then
        # https://stackoverflow.com/a/8542420/17619982
        local temp=$(networksetup -getairportnetwork en0)
        python3 -c "print('$temp'.split(':',1)[1].strip() if ':' in '$temp' else 'unknown')"
    else
        echo "unknown"
    fi
}

export BLUER_AI_WIFI_SSID=$(bluer_ai_wifi_get_ssid)
echo "🌀 wifi: $BLUER_AI_WIFI_SSID"
