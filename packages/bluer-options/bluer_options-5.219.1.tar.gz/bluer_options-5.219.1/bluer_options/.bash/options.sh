#! /usr/bin/env bash

function bluer_ai_option() {
    python3 -m bluer_options.options \
        get \
        --options "$1" \
        --keyword "$2" \
        --default "$3" \
        "${@:4}"
}

function bluer_ai_option_choice() {
    python3 -m bluer_options.options \
        choice \
        --options "$1" \
        --choices "$2" \
        --default "$3" \
        "${@:4}"
}

function bluer_ai_option_int() {
    python3 -m bluer_options.options \
        get \
        --options "$1" \
        --keyword "$2" \
        --default "$3" \
        --is_int 1 \
        "${@:4}"
}
