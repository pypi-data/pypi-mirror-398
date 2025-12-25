#! /usr/bin/env bash

function bluer_ai_eval() {
    local options=$1
    local do_dryrun=$(bluer_ai_option_int "$options" dryrun 0)
    local do_log=$(bluer_ai_option_int "$options" log 1)
    local path=$(bluer_ai_option "$options" path ./)
    local in_background=$(bluer_ai_option_int "$options" background 0)

    [[ "$path" != "./" ]] && mkdir -pv $path

    local command_line="${@:2}"

    if [[ "$do_log" == 1 ]]; then
        if [[ "$in_background" == 1 ]]; then
            bluer_ai_log "⚙️ in background: $command_line"
        else
            bluer_ai_log "⚙️ $command_line"
        fi

        [[ "$path" != "./" ]] && bluer_ai_log " 📂 $path"
    fi

    [[ "$do_dryrun" == 1 ]] && return

    [[ "$path" != "./" ]] && pushd $path >/dev/null

    if [[ "$in_background" == 1 ]]; then
        (
            source \
                $abcli_path_bash/bluer_ai.sh \
                ~terraform,$options \
                "$command_line"
        ) &
    else
        eval "$command_line"
        local status="$?"

        [[ "$path" != "./" ]] && popd >/dev/null

        if [[ $status -ne 0 ]]; then
            bluer_ai_log_error "@eval: failed: status=$status: $command_line"
            return 1
        fi

        return 0
    fi
}
