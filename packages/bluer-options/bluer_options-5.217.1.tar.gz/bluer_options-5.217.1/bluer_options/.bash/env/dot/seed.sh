#! /usr/bin/env bash

# internal function for bluer_ai_seed.
function bluer_ai_env_dot_seed() {
    # seed is NOT local

    local path=$1

    if [[ ! -d "$path" ]]; then
        bluer_ai_log_error "$path not found."
        return 1
    fi

    pushd $path >/dev/null
    local line
    local var_name
    local var_value
    for line in $(dotenv \
        --file sample.env \
        list \
        --format shell); do

        var_name=$(python -c "print('$line'.split('=',1)[0])")

        var_value=${!var_name}

        seed="${seed}export $var_name=$var_value$delim"
    done
    popd >/dev/null

    seed="$seed$delim"
}
