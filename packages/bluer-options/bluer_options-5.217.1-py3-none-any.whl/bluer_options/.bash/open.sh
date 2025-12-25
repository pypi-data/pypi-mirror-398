#! /usr/bin/env bash

function bluer_ai_open() {
    local options=$1

    local extension=$(bluer_ai_option "$options" extension)
    local open_QGIS=$(bluer_ai_option_int "$options" QGIS 0)
    [[ $open_QGIS == 1 ]] &&
        extension="qgz"

    local object_name=$(bluer_ai_clarify_object $2 .)

    local filename=""
    [[ ! -z "$extension" ]] &&
        filename=$object_name.$extension
    filename=$(bluer_ai_option "$options" filename $filename)

    local what=$ABCLI_OBJECT_ROOT/$object_name
    [[ ! -z "$filename" ]] &&
        what=$what/$filename

    if [[ "$abcli_is_github_workflow" == true ]]; then
        bluer_ai_log_warning "@open: $what: skipped."
    else
        bluer_ai_log "📜 $what"
        open "$what"
    fi
}
