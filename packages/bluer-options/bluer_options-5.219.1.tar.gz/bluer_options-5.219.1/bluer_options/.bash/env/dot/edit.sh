#! /usr/bin/env bash

function bluer_ai_env_dot_edit() {
    local machine_kind=$(bluer_ai_clarify_input $1 local)

    local machine_name=$2

    if [ "$machine_kind" == "local" ]; then
        bluer_ai_code $abcli_path_abcli/.env
    else
        local filename="$abcli_object_temp/scp-${machine_kind}-${machine_name}.env"

        abcli_scp \
            $machine_kind \
            $machine_name \
            \~/git/awesome-bash-cli/.env \
            - \
            - \
            $filename

        bluer_ai_code $filename

        abcli_scp \
            local \
            - \
            $filename \
            $machine_kind \
            $machine_name \
            \~/git/awesome-bash-cli/.env
    fi
}
