#! /usr/bin/env bash

function bluer_ai_list() {
    local task=$1

    local function_name=bluer_ai_list_$task
    if [[ $(type -t $function_name) == "function" ]]; then
        $function_name "${@:2}"
        return
    fi

    python3 -m bluer_options.list "$@"
}

function bluer_ai_list_filter() {
    python3 -m bluer_options.list \
        filter \
        --items "$1" \
        "${@:2}"
}

function bluer_ai_list_in() {
    python3 -m bluer_options.list \
        in \
        --item "$1" \
        --items "$2" \
        "${@:3}"
}

function bluer_ai_list_intersect() {
    python3 -m bluer_options.list \
        intersect \
        --items_1 "$1" \
        --items_2 "$2" \
        "${@:3}"
}

function bluer_ai_list_item() {
    python3 -m bluer_options.list \
        item \
        --items "$1" \
        --index "$2" \
        "${@:3}"
}

function bluer_ai_list_len() {
    python3 -m bluer_options.list \
        len \
        --items "$1" \
        "${@:2}"
}

function bluer_ai_list_log() {
    bluer_ai_log_list "$@"
}

function bluer_ai_list_next() {
    python3 -m bluer_options.list \
        next \
        --item "$1" \
        --items "$2" \
        "${@:3}"
}

function bluer_ai_list_prev() {
    python3 -m bluer_options.list \
        prev \
        --item "$1" \
        --items "$2" \
        "${@:3}"
}

function bluer_ai_list_nonempty() {
    python3 -m bluer_options.list \
        nonempty \
        --items "$1" \
        "${@:2}"
}

function bluer_ai_list_resize() {
    python3 -m bluer_options.list \
        resize \
        --items "$1" \
        --count "$2" \
        "${@:3}"
}

function bluer_ai_list_reverse() {
    python3 -m bluer_options.list \
        reverse \
        --items "$1" \
        "${@:2}"
}

function bluer_ai_list_sort() {
    python3 -m bluer_options.list \
        sort \
        --items "$1" \
        "${@:2}"
}
