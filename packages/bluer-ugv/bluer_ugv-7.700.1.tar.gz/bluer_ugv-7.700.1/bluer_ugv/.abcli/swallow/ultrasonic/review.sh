#! /usr/bin/env bash

function bluer_ugv_swallow_ultrasonic_review() {
    local options=$1
    local do_download=$(bluer_ai_option_int "$options" download 1)
    local do_upload=$(bluer_ai_option_int "$options" upload 0)

    local object_name=$(bluer_ai_clarify_object $2 .)
    [[ "$do_download" == 1 ]] &&
        bluer_objects_download \
            - \
            $object_name

    bluer_ai_eval dryrun=$do_dryrun \
        python3 -m bluer_ugv.swallow.session.classical.ultrasonic_sensor \
        review \
        --object_name $object_name \
        "${@:3}"
    local status="$?"

    [[ "$do_upload" == 1 ]] &&
        bluer_objects_upload \
            - \
            $object_name

    return $status
}
