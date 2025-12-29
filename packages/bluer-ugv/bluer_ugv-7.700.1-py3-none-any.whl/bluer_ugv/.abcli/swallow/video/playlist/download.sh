#! /usr/bin/env bash

function bluer_ugv_swallow_video_playlist_download() {
    local options=${1:-policy=doesnt_exist}

    [[ "$abcli_is_rpi" == true ]] &&
        sudo chown pi:pi \
            $ABCLI_OBJECT_ROOT/$RANGIN_VIDEO_LIST_OBJECT

    bluer_objects_download \
        filename=metadata.yaml \
        $RANGIN_VIDEO_LIST_OBJECT
    [[ $? -ne 0 ]] && return 1

    bluer_objects_download \
        ,$options \
        $RANGIN_VIDEO_LIST_OBJECT
}
