#! /usr/bin/env bash

function bluer_ugv_git() {
    local options=$1
    local designs=$(bluer_ai_option_int "$options" designs 0)

    local repo_name=bluer-ugv
    [[ "$designs" == 1 ]] &&
        repo_name=$repo_name-mechanical-design

    bluer_ai_git \
        $repo_name \
        "${@:2}"
}
