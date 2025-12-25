#! /usr/bin/env bash

function bluer_ai_install_module() {
    [[ "$abcli_is_in_notebook" == true ]] && return

    local module=$1

    local version=${2-"1.1.1"}

    local install_path=$HOME/_bluer_ai_install_checkpoint
    mkdir -pv $install_path

    local install_checkpoint=$install_path/${module}-${version}

    local description="$module-terraform-$version"

    if [ -f "$install_checkpoint" ]; then
        bluer_ai_log "🌀 $description"
    else
        bluer_ai_log "installing $description..."

        eval bluer_ai_install_$module

        touch $install_checkpoint
    fi
}
