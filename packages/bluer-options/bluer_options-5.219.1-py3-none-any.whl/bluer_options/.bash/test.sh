#! /usr/bin/env bash

function bluer_ai_test() {
    local options=$1
    local plugin_name=$(bluer_ai_option "$options" plugin bluer_ai)

    local test_options=$2

    if [ $(bluer_ai_option_int "$options" list 0) == 1 ]; then
        local plugin_name_=$(echo $plugin_name | tr - _)
        declare -F | awk '{print $3}' | grep test_${plugin_name_}
        return
    fi

    bluer_ai_log "testing $plugin_name ..."

    local do_dryrun=$(bluer_ai_option_int "$options" dryrun 0)

    local list_of_tests=$(bluer_ai_option "$options" what all)
    [[ "$list_of_tests" == all ]] &&
        list_of_tests=$(bluer_ai_test list,plugin=$plugin_name | tr "\n" " ")
    bluer_ai_log_list "$list_of_tests" \
        --delim space \
        --before "running" \
        --after "test(s)"

    local test_name
    local failed_test_list=
    for test_name in $list_of_tests; do
        bluer_ai_eval dryrun=$do_dryrun \
            $test_name \
            "$test_options" \
            "${@:3}"
        if [ $? -ne 0 ]; then
            bluer_ai_log_error "$test_name: failed."
            failed_test_list=$failed_test_list,$test_name
        fi

        bluer_ai_hr
    done

    failed_test_list=$(bluer_ai_list_nonempty $failed_test_list)
    if [[ -z "$failed_test_list" ]]; then
        bluer_ai_log "✅ $plugin_name"
        return
    else
        bluer_ai_log_list "$failed_test_list" \
            --after "failed test(s)" \
            --before ""
        return 1
    fi
}
