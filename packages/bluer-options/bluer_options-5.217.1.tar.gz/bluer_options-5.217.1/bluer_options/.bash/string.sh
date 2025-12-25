#! /usr/bin/env bash

function bluer_ai_string_after() {
    python3 -m bluer_options.string \
        after \
        --string "$1" \
        --substring "$2" \
        "${@:3}"
}

function bluer_ai_string_before() {
    python3 -m bluer_options.string \
        before \
        --string "$1" \
        --substring "$2" \
        "${@:3}"
}

function bluer_ai_string_random() {
    python3 -m bluer_options.string \
        random \
        "$@"
}

function bluer_ai_string_timestamp() {
    python3 -m bluer_options.string \
        pretty_date \
        --unique 1 \
        "$@"
}

function bluer_ai_string_timestamp_short() {
    python3 -m bluer_options.string \
        pretty_date \
        --include_time 0 \
        --unique 1 \
        "$@"
}

function bluer_ai_string_today() {
    python3 -m bluer_options.string \
        pretty_date \
        --include_time 0 \
        "$@"
}
