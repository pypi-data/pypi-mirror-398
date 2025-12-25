#! /usr/bin/env bash

function bluer_ai_env_dot_load() {
    local options=$1
    local plugin_name=$(bluer_ai_option "$options" plugin abcli)
    local use_caller=$(bluer_ai_option_int "$options" caller 0)
    local use_ssm=$(bluer_ai_option_int "$options" ssm 0)
    local suffix=$(bluer_ai_option "$options" suffix)
    local path
    if [[ "$use_caller" == 1 ]]; then
        path=$(dirname "$(realpath "${BASH_SOURCE[1]}")")$suffix
    else
        local repo_name=$(bluer_ai_unpack_repo_name $plugin_name)

        path=$abcli_path_git/$repo_name
    fi

    local filename=$(bluer_ai_option "$options" filename .env)
    local verbose=$(bluer_ai_option_int "$options" verbose 0)

    if [[ ! -f "$path/$filename" ]]; then
        if [[ "$use_ssm" == 1 ]]; then
            local module_name=$(bluer_ai_get_module_name_from_plugin $plugin_name)
            bluer_ai_ssm_get path=$path/$module_name
        else
            bluer_ai_log_warning "@env: dot: load: $path/$filename: file not found."
        fi
        return
    fi

    pushd $path >/dev/null
    local line
    local count=0
    for line in $(dotenv \
        --file $filename \
        list \
        --format shell); do
        [[ $verbose == 1 ]] && bluer_ai_log "$line"

        export "$line"
        ((count++))
    done
    popd >/dev/null

    bluer_ai_log "@env: dot: load: $count var(s): $path/$filename"
}
