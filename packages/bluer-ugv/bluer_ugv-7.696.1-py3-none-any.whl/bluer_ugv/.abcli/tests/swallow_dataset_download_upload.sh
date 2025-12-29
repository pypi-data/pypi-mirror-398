#! /usr/bin/env bash

function test_bluer_ugv_swallow_dataset_download_upload() {
    local options=$1

    local mode
    for mode in navigation yolo; do
        bluer_ugv_swallow_dataset_download $mode
        [[ $? -ne 0 ]] && return 1

        bluer_ugv_swallow_dataset_upload $mode
        [[ $? -ne 0 ]] && return 1

        bluer_ai_hr
    done
}
