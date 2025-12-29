#! /usr/bin/env bash

function bluer_ugv_swallow_env_set() {
    local var_name=${1:-void}

    if [[ "$var_name" == "bps" ]]; then
        var_name=BLUER_SBC_SWALLOW_HAS_BPS
    elif [[ "$var_name" == "camera" ]]; then
        var_name=BLUER_SBC_SWALLOW_HAS_CAMERA
    elif [[ "$var_name" == "full_keyboard" ]]; then
        var_name=BLUER_SBC_SWALLOW_HAS_FULL_KEYBOARD
    elif [[ "$var_name" == "screen" ]]; then
        var_name=BLUER_SBC_ENABLE_SCREEN
    elif [[ "$var_name" == "steering" ]]; then
        var_name=BLUER_SBC_SWALLOW_HAS_STEERING
    else
        bluer_ai_log_error "$var_name: var not found."
        return 1
    fi

    pushd $abcli_path_git/bluer-sbc >/dev/null

    dotenv set \
        $var_name \
        "${@:2}"
    [[ $? -ne 0 ]] && return 1

    popd >/dev/null

    bluer_sbc init
}
