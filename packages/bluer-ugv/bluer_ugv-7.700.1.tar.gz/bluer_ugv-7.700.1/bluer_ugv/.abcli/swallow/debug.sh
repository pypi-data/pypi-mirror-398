#! /usr/bin/env bash

function bluer_ugv_swallow_debug() {
    local options=$1
    local do_upload=$(bluer_ai_option_int "$options" upload 1)

    local object_name=$(bluer_ai_clarify_object $2 swallow-debug-$(bluer_ai_string_timestamp))

    bluer_ai_eval dryrun=$do_dryrun \
        python3 -m bluer_ugv.swallow \
        debug \
        --object_name $object_name \
        "${@:3}"
    local status="$?"

    [[ "$do_upload" == 1 ]] &&
        bluer_objects_upload \
            filename=$object_name.gif \
            $object_name

    return $status
}
