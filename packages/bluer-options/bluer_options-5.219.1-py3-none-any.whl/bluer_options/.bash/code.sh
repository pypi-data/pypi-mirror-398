#! /usr/bin/env bash

function bluer_ai_code() {
    bluer_ai_log "editing $@"

    if [[ "$abcli_is_mac" == true ]]; then
        /Applications/Visual\ Studio\ Code.app/Contents/Resources/app/bin/code "$@"
    elif [[ "$abcli_is_github_workflow" == true ]]; then
        bluer_ai_log_warning "@code: $@: skipped."
    else
        nano "$@"
    fi
}
