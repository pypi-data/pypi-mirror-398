#! /usr/bin/env bash

function bluer_ai_watch() {
    local options=$1
    local do_clear=$(bluer_ai_option_int "$options" clear 1)

    while true; do
        [[ "$do_clear" == 1 ]] && clear

        bluer_ai_eval "$@"

        bluer_ai_sleep ,$options
    done
}
