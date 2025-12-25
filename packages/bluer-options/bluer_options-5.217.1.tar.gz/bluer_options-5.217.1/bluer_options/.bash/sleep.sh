#! /usr/bin/env bash

function bluer_ai_sleep() {
    local options=$1
    local seconds=$(bluer_ai_option "$options" seconds 3)

    bluer_ai_log_local "sleeping for $seconds s ... (^C to stop)"
    sleep $seconds
}
