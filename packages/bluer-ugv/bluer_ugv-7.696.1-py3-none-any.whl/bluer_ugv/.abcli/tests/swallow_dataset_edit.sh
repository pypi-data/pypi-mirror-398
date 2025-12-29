#! /usr/bin/env bash

function test_bluer_ugv_swallow_dataset_edit() {
    local options=$1

    local mode
    for mode in navigation yolo; do
        bluer_ugv_swallow_dataset_edit $mode

        bluer_ai_hr
    done
}
