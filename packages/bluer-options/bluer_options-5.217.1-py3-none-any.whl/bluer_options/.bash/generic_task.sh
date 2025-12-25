#! /usr/bin/env bash

function bluer_ai_generic_task() {
    local options=$1
    local plugin_name=$(bluer_ai_option "$options" plugin abcli)
    local task=$(bluer_ai_option "$options" task unknown)

    local function_name="${plugin_name}_${task}"
    if [[ $(type -t $function_name) == "function" ]]; then
        $function_name "${@:2}"
        return
    fi

    if [ "$task" == "build_README" ]; then
        bluer_ai_build_README \
            plugin=$plugin_name,$2 \
            "${@:3}"
        return
    fi

    if [ "$task" == "init" ]; then
        bluer_ai_init $plugin_name "${@:2}"

        [[ "$abcli_is_docker" == false ]] &&
            [[ $(bluer_ai_conda exists $plugin_name) == 1 ]] &&
            conda activate $plugin_name

        return 0
    fi

    if [[ "|pylint|pytest|test|" == *"|$task|"* ]]; then
        bluer_ai_${task} plugin=$plugin_name,$2 \
            "${@:3}"
        return
    fi

    if [[ "|pypi|" == *"|$task|"* ]]; then
        bluer_ai_${task} "$2" \
            plugin=$plugin_name,$3 \
            "${@:4}"
        return
    fi

    local module_name=$(bluer_ai_get_module_name_from_plugin $plugin_name)
    python3 -m $module_name "$task" "${@:2}"
}
