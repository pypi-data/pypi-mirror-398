#! /usr/bin/env bash

function bluer_ugv_swallow_dataset_download() {
    local options=$1
    local do_metadata=$(bluer_ai_option_int "$options" metadata 1)
    local mode=$(bluer_ai_option_choice "$options" navigation,yolo yolo)

    local object_name=$BLUER_UGV_SWALLOW_YOLO_DATASET_LIST
    [[ "$mode" == "navigation" ]] &&
        object_name=$BLUER_UGV_SWALLOW_NAVIGATION_DATASET_LIST

    local download_options="-"
    [[ "$do_metadata" == 1 ]] &&
        download_options="filename=metadata.yaml"

    bluer_objects_download \
        $download_options \
        $object_name
}
