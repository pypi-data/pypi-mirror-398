#! /usr/bin/env bash

function bluer_ugv_swallow_keyboard() {
    local task=$1

    local function_name=bluer_ugv_swallow_keyboard_$task
    if [[ $(type -t $function_name) == "function" ]]; then
        $function_name "${@:2}"
        return
    fi

    sudo -E $(which python3) \
        -m bluer_ugv.swallow.session.classical.keyboard \
        "$@"
}

bluer_ai_source_caller_suffix_path /keyboard
