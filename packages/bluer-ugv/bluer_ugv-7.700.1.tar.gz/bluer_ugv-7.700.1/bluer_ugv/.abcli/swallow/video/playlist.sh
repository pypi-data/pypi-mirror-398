#! /usr/bin/env bash

function bluer_ugv_swallow_video_playlist() {
    local task=$1

    local function_name=bluer_ugv_swallow_video_playlist_$task
    if [[ $(type -t $function_name) == "function" ]]; then
        $function_name "${@:2}"
        return
    fi

    python3 -m bluer_ugv.swallow.session.classical.screen.video "$@"
}

bluer_ai_source_caller_suffix_path /playlist
