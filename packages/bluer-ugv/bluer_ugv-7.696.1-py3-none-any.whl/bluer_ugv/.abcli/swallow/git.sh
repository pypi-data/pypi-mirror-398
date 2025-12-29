#! /usr/bin/env bash

function bluer_ugv_swallow_git() {
    local task=$1

    local function_name=bluer_ugv_swallow_git_$task
    if [[ $(type -t $function_name) == "function" ]]; then
        $function_name "${@:2}"
        return
    fi

    bluer_ai_log_error "@swallow: git: $task: command not found."
    return 1
}

bluer_ai_source_caller_suffix_path /git
