#! /usr/bin/env bash

function bluer_ugv_swallow_dataset_list() {
    local options=$1
    local do_download=$(bluer_ai_option_int "$options" download 1)
    local mode=$(bluer_ai_option_choice "$options" navigation,yolo yolo)

    local object_name=$BLUER_UGV_SWALLOW_YOLO_DATASET_LIST
    [[ "$mode" == "navigation" ]] &&
        object_name=$BLUER_UGV_SWALLOW_NAVIGATION_DATASET_LIST

    if [[ "$do_download" == 1 ]]; then
        bluer_ugv_swallow_dataset_download $mode
        [[ $? -ne 0 ]] && return 1
    fi

    bluer_objects_metadata_get \
        key=dataset-list,object \
        $object_name
}
