#! /usr/bin/env bash

function bluer_ugv_swallow_session() {
    local task=${1:-start}

    local options=$2
    local do_dryrun=$(bluer_ai_option_int "$options" dryrun 0)
    local do_upload=$(bluer_ai_option_int "$options" upload 1)

    bluer_ai_log "@ugv: swallow: session @ $abcli_object_name started ..."

    bluer_objects_mlflow_tags_set \
        $abcli_object_name \
        session,host=$abcli_hostname,$BLUER_SBC_SESSION_OBJECT_TAGS

    if [[ "$BLUER_SBC_SWALLOW_HAS_BPS" == 1 ]]; then
        bluer_ai_log "🏓 starting bps in the background"

        bluer_ai_eval \
            background,dryrun=$do_dryrun \
            bluer_algo_bps \
            loop \
            start \
            ~upload \
            $abcli_object_name
    fi

    local sudo_prefix=""
    [[ "$BLUER_AI_SESSION_IS_SUDO" == 1 ]] &&
        sudo_prefix="sudo -E"

    bluer_ai_eval dryrun=$do_dryrun \
        $sudo_prefix \
        $(which python3) -m bluer_ugv.swallow.session \
        ${task}_session \
        "${@:3}"
    local status="$?"

    if [[ "$BLUER_SBC_SWALLOW_HAS_BPS" == 1 ]]; then
        bluer_ai_log "🏓 stopping bps ..."

        sudo chown pi \
            $ABCLI_OBJECT_ROOT/$abcli_object_name/metadata.yaml

        bluer_ai_eval dryrun=$do_dryrun \
            bluer_algo_bps \
            loop \
            stop \
            wait

        bluer_ai_log "🏓 bps stopped."
    fi

    [[ "$do_upload" == 1 ]] &&
        bluer_objects_upload - $abcli_object_name

    bluer_ai_log "@ugv: swallow: session ended."

    return $status
}
