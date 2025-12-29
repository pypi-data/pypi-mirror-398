#! /usr/bin/env bash

function test_bluer_ugv_ultrasonic_sensor_review() {
    local options=$1

    bluer_ai_eval ,$options \
        bluer_ugv_swallow_ultrasonic_review \
        download \
        $BLUER_UGV_ULTRASONIC_SENSOR_TEST_OBJECT
}
