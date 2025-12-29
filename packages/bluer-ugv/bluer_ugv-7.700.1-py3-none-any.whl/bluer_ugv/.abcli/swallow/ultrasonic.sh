#! /usr/bin/env bash

function bluer_ugv_swallow_ultrasonic() {
    local task=$1

    local function_name=bluer_ugv_swallow_ultrasonic_$task
    if [[ $(type -t $function_name) == "function" ]]; then
        $function_name "${@:2}"
        return
    fi

    python3 -m bluer_ugv.swallow.session.classical.ultrasonic_sensor "$@"
}

bluer_ai_source_caller_suffix_path /ultrasonic
