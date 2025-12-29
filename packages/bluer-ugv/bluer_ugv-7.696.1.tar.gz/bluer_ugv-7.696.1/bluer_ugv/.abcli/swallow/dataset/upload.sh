#! /usr/bin/env bash

function bluer_ugv_swallow_dataset_upload() {
    local options=$1
    local do_metadata=$(bluer_ai_option_int "$options" metadata 1)
    local mode=$(bluer_ai_option_choice "$options" navigation,yolo yolo)

    local object_name=$BLUER_UGV_SWALLOW_YOLO_DATASET_LIST
    [[ "$mode" == "navigation" ]] &&
        object_name=$BLUER_UGV_SWALLOW_NAVIGATION_DATASET_LIST

    local upload_options="-"
    [[ "$do_metadata" == 1 ]] &&
        upload_options="filename=metadata.yaml"

    bluer_objects_upload \
        $upload_options \
        $object_name
}
