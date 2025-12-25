#! /usr/bin/env bash

function bluer_ai_env_dot_cat() {
    local env_name=$(bluer_ai_clarify_input $1 .env)

    if [[ "$env_name" == ".env" ]]; then
        pushd $abcli_path_abcli >/dev/null
        bluer_ai_eval - \
            dotenv list --format shell
        popd >/dev/null
        return
    fi

    if [ "$(bluer_ai_list_in $env_name rpi,jetson_nano)" == True ]; then
        local machine_kind=$1
        local machine_name=$2

        local filename="$abcli_path_temp/scp-${machine_kind}-${machine_name}.env"

        abcli_scp \
            $machine_kind \
            $machine_name \
            \~/git/bluer_ai/.env \
            - \
            - \
            $filename

        cat $filename

        return
    fi

    if [[ "$env_name" == "config" ]]; then
        bluer_ai_eval - \
            cat $abcli_path_abcli/bluer_ai/config.env
        return
    fi

    if [[ "$env_name" == "sample" ]]; then
        bluer_ai_eval - \
            cat $abcli_path_abcli/sample.env
        return
    fi

    bluer_ai_eval - \
        cat $abcli_path_assets/env/$env_name.env
}
