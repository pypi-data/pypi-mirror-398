#! /usr/bin/env bash

function bluer_ugv_swallow_keyboard_test() {
    bluer_ai_eval ,$1 \
        sudo -E $(which python3) \
        -m bluer_ugv.swallow.session.classical.keyboard \
        test \
        "${@:2}"
}
