#! /usr/bin/env bash

function bluer_ai_pytest() {
    local options=$1

    local plugin_name=$(bluer_ai_option "$options" plugin bluer_ai)

    local args="${@:2}"

    [[ $(bluer_ai_option_int "$options" list 0) == 1 ]] &&
        args="$args --collect-only"

    [[ $(bluer_ai_option_int "$options" show_warning 0) == 0 ]] &&
        args="$args --disable-warnings"

    [[ $(bluer_ai_option_int "$options" verbose 1) == 1 ]] &&
        args="$args --verbose"

    local repo_name=$(bluer_ai_unpack_repo_name $plugin_name)
    bluer_ai_log "$plugin_name: pytest: repo=$repo_name"

    # https://stackoverflow.com/a/40720333/17619982
    bluer_ai_eval "path=$abcli_path_git/$repo_name,$options" \
        python3 -m pytest "$args"
}

# https://stackoverflow.com/a/40724361/10917551
# --disable-pytest-warnings"
