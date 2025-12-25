#! /usr/bin/env bash

function bluer_ai_repeat() {
    local options=$1
    local count=$(bluer_ai_option "$options" count 1)

    # https://stackoverflow.com/a/3737773/17619982
    for index in $(seq $count); do
        bluer_ai_log "🔄 $index / $count"
        bluer_ai_eval "$@"
    done
}
