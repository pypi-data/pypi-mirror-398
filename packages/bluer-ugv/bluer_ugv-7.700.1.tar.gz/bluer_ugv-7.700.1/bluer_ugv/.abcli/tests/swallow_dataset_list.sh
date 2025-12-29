#! /usr/bin/env bash

function test_bluer_ugv_swallow_dataset_list() {
    local options=$1

    local mode
    for mode in navigation yolo; do
        bluer_ugv_swallow_dataset_list $mode
        [[ $? -ne 0 ]] && return 1

        bluer_ai_hr
    done
}
