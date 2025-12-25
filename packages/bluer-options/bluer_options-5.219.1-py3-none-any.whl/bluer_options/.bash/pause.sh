#! /usr/bin/env bash

function bluer_ai_pause() {
    local options=$1
    local do_dryrun=$(bluer_ai_option_int "$options" dryrun 0)

    local message=$(bluer_ai_option "$options" message "press any key to continue...")
    message=$(echo $message | tr - " ")
    bluer_ai_log "$message"

    if [[ "$do_dryrun" = 0 ]]; then
        read -p ""
    fi
}
