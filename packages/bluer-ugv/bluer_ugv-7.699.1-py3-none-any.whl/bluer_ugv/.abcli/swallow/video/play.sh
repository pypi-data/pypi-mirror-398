#! /usr/bin/env bash

function bluer_ugv_swallow_video_play() {
    python3 -m bluer_ugv.swallow.session.classical.screen.video \
        play \
        "$@"
}
