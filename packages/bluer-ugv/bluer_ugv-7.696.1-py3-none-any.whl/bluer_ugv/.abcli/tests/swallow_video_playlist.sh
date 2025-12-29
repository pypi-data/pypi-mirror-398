#! /usr/bin/env bash

function test_swallow_video_playlist_cat() {
    local options=$1

    bluer_ai_eval ,$options \
        bluer_ugv \
        swallow \
        video \
        playlist \
        cat
}

function test_swallow_video_playlist_download_upload() {
    local options=$1

    bluer_ai_eval ,$options \
        bluer_ugv \
        swallow \
        video \
        playlist \
        download \
        policy=doesnt_exist
    [[ $? -ne 0 ]] && return 1

    bluer_ai_eval ,$options \
        bluer_ugv \
        swallow \
        video \
        playlist \
        upload \
        filename=metadata.yaml
}

function test_swallow_video_playlist_edit() {
    local options=$1

    bluer_ai_eval ,$options \
        bluer_ugv \
        swallow \
        video \
        playlist \
        edit \
        download
}
