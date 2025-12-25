#! /usr/bin/env bash

# wrap-around
export ABCUL=" \\\\\n\t"
export ABCUL2=" \n   "
export ABCUL3=" \n      "

# https://chatgpt.com/share/d354d916-3003-4a6d-84f3-5c51a59ed4b1
function xwrap {
    local output=""
    for arg in "$@"; do
        output+="${ABCUL}[${arg}]"
    done
    echo "$output"
}

# extra options
export EOP=$YELLOW
export EOPE=$LIGHTBLUE
export EARGS="$ABCUL$EOP[<args>]$EOPE"

function xtra() {
    echo "$EOP$*$EOPE"
}

if [[ "$abcli_is_colorful" == true ]]; then
    export BLUE='\033[1;34m'
    export LIGHTBLUE='\033[1;96m'
    export CYAN='\033[0;36m'
    export GREEN='\033[0;32m'
    export NC='\033[0m'
    export RED='\033[0;31m'
    export YELLOW='\033[0;33m'
else
    unset BLUE LIGHTBLUE CYAN GREEN NC RED YELLOW
fi

function bluer_ai_cat() {
    local filename=$1

    if [ ! -f "$filename" ]; then
        bluer_ai_log_error "@cat: $filename: file not found."
        return 1
    fi

    printf "🗒️  $CYAN$filename$NC\n$BLUE"
    cat $filename
    printf "$NC\n🗒️  $CYAN/$filename$NC\n"
}

function bluer_ai_hr() {
    local width=80
    [[ "$abcli_is_github_workflow" == false ]] &&
        [[ "$abcli_is_aws_batch" == false ]] &&
        width=$(tput cols)

    python3 -m bluer_options.terminal hr \
        --width $width
}

function bluer_ai_log_list() {
    local message=$(python3 -m bluer_options.list \
        log \
        --items "$1" \
        "${@:2}")

    printf "$message\n"
}

function bluer_ai_log_local() {
    local message="$@"
    printf "$CYAN$message$NC\n"
}
