#! /usr/bin/env bash

function bluer_ai_not() {
    if [ "$1" == 1 ] || [ "$1" == true ]; then
        echo 0
    else
        echo 1
    fi
}
