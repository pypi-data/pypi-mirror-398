#! /usr/bin/env bash

function bluer_ai_env_dot_cp() {
    local env_name=$1
    [[ "$env_name" == *.env ]] &&
        env_name="${env_name%.env}"

    local machine_kind=$(bluer_ai_clarify_input $2 local)

    local machine_name=$3

    if [ "$machine_kind" == "local" ]; then
        cp -v \
            $abcli_path_assets/env/$env_name.env \
            $abcli_path_git/bluer-sbc/.env
    else
        # https://kb.iu.edu/d/agye
        abcli_scp \
            local \
            - \
            $abcli_path_assets/env/$env_name.env \
            $machine_kind \
            $machine_name \
            \~/git/bluer-sbc/.env
    fi
}
