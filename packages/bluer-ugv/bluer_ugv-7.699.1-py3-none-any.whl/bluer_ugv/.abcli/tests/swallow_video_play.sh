#! /usr/bin/env bash

function test_swallow_video_play() {
    local options=$1

    bluer_ai_eval ,$options \
        bluer_ugv \
        swallow \
        video \
        play
}
