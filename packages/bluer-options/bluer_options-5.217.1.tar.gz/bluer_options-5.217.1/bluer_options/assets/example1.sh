#! /usr/bin/env bash

export abcli_is_colorful=true

alias @git=my_git

source $(python3 -m bluer_options locate)/.bash/bluer_options.sh

function my_git() {
    local task=${1:-help}

    if [[ "$task" == "commit" ]]; then
        local message=${1:-"Initial commit"}

        local options=$2
        local do_push=$(bluer_ai_options_int "$options" push 1)

        git add .

        git commit -m "$message"

        [[ "$do_push" == 1 ]] && git push

        return 0
    fi

    git "$@"
}
