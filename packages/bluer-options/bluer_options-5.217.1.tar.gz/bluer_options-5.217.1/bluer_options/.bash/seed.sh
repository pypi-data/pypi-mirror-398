#! /usr/bin/env bash

function bluer_ai_seed() {
    local task=$1

    # internal function
    if [[ "$task" == "add_bluer_ai_env" ]]; then
        seed="${seed}python3 -m venv \$HOME/venv/bluer_ai$delim"
        seed="${seed}source \$HOME/venv/bluer_ai/bin/activate$delim_section"
        return
    fi
    if [[ "$task" == "add_bluer_ai_env_ssp" ]]; then
        seed="${seed}python3 -m venv \$HOME/venv/bluer_ai --system-site-packages$delim"
        seed="${seed}source \$HOME/venv/bluer_ai/bin/activate$delim_section"
        return
    fi

    # internal function.
    if [[ "$task" == "add_file" ]]; then
        local base64="base64"
        # https://superuser.com/a/1225139
        [[ "$abcli_is_ubuntu" == true ]] && base64="base64 -w 0"

        local source_filename=$2

        local destination_filename=$3

        local var_name=_bluer_ai_seed_$(echo $source_filename | tr / _ | tr . _ | tr - _ | tr \~ _ | tr \$ _)

        local seed="$var_name=\"$(cat $source_filename | $base64)\"$delim"
        seed="${seed}echo \$$var_name | base64 --decode > $var_name$delim"
        seed="$seed${sudo_prefix}mv -v $var_name $destination_filename"

        echo $seed
        return
    fi

    # internal function.
    if [[ "$task" == "add_kaggle" ]]; then
        if [[ -f "$HOME/.kaggle/kaggle.json" ]]; then
            seed="${seed}mkdir -p \$HOME/.kaggle$delim"
            seed="$seed$(bluer_ai_seed add_file $HOME/.kaggle/kaggle.json \$HOME/.kaggle/kaggle.json)$delim"
            seed="${seed}chmod 600 \$HOME/.kaggle/kaggle.json$delim_section"
        else
            bluer_ai_log_warning "@seed: kaggle.json not found."
        fi
        return
    fi

    # internal function.
    if [[ "$task" == "add_repo" ]]; then
        local options=$2
        local do_clone=$(bluer_ai_option "$options" clone 1)
        local use_ssh=$(bluer_ai_option_int "$options" ssh 1)
        local repo_name=$(bluer_ai_option "$options" repo bluer-ai)

        if [[ "$do_clone" == 0 ]]; then
            seed="${seed}cd; cd git/$repo_name${delim}"
            return
        fi

        local repo_address="git@github.com:kamangir/$repo_name.git"
        [[ "$use_ssh" == 0 ]] &&
            repo_address="https://github.com/kamangir/$repo_name"

        local repo_branch=$(bluer_ai_git $repo_name get_branch)

        seed="${seed}cd; mkdir -p git; cd git$delim"
        seed="${seed}git clone $repo_address$delim"
        seed="${seed}cd $repo_name$delim"
        seed="${seed}git checkout $repo_branch$delim"
        seed="${seed}git config pull.rebase false$delim"
        seed="${seed}git pull$delim_section"

        return
    fi

    # internal function.
    if [[ "$task" == "add_ssh_key" ]]; then
        local options=$2
        local sudo_mode=$(bluer_ai_option_int "$options" sudo 0)

        seed="${seed}${sudo_prefix}mkdir -p ~/.ssh$delim_section"
        seed="$seed"'eval "$(ssh-agent -s)"'"$delim_section"
        seed="$seed$(bluer_ai_seed add_file $HOME/.ssh/$BLUER_AI_GIT_SSH_KEY_NAME \$HOME/.ssh/$BLUER_AI_GIT_SSH_KEY_NAME)$delim"
        seed="${seed}chmod 600 ~/.ssh/$BLUER_AI_GIT_SSH_KEY_NAME$delim"
        seed="${seed}ssh-add -k ~/.ssh/$BLUER_AI_GIT_SSH_KEY_NAME$delim"

        if [[ "$sudo_mode" == 1 ]]; then
            seed="${seed}ssh-keyscan github.com | sudo tee -a ~/.ssh/known_hosts$delim"
        else
            seed="${seed}ssh-keyscan github.com >> ~/.ssh/known_hosts$delim"
        fi

        seed="${seed}"'ssh -T git@github.com'"$delim_section"
        return
    fi

    if [[ "$task" == "eject" ]]; then
        if [[ "$abcli_is_jetson" == true ]]; then
            sudo eject /media/bluer_ai/SEED
        else
            sudo diskutil umount /Volumes/seed
        fi
        return
    fi

    if [[ "$task" == "list" ]]; then
        local list_of_targets=$(declare -F | awk '{print $NF}' | grep 'bluer_ai_seed_' | sed 's/bluer_ai_seed_//' | tr '\n' '|')

        bluer_ai_log_list "$list_of_targets" \
            --before "" \
            --delim \| \
            --after "target(s)" \
            --sorted 1
        return
    fi

    local seed=""

    local target=$(bluer_ai_clarify_input $1 ec2)

    local options=$2
    local do_log=$(bluer_ai_option_int "$options" log 1)
    local do_eval=$(bluer_ai_option_int "$options" eval 0)
    local include_aws=$(bluer_ai_option_int "$options" aws 0)
    local output=$(bluer_ai_option_choice "$options" clipboard,key,screen clipboard)

    local delim="\n"
    local delim_section="\n\n"
    if [ "$output" == "clipboard" ]; then
        delim="; "
        delim_section="; "
    fi

    local env_name=$(bluer_ai_option "$options" env "")

    local sudo_prefix="sudo "

    if [ "$output" == "key" ]; then
        local seed_path="/Volumes/seed"
        [[ "$abcli_is_jetson" == true ]] &&
            seed_path="/media/bluer_ai/SEED"

        if [ ! -d "$seed_path" ]; then
            bluer_ai_log_error "@seed: usb key not found."
            return 1
        fi

        mkdir -p $seed_path/bluer_ai/
    fi

    [[ "$do_log" == 1 ]] &&
        bluer_ai_log "$abcli_fullname seed 🌱 -$output-> $target"

    local seed="#! /bin/bash$delim"
    [[ "$output" == "clipboard" ]] && seed=""

    seed="${seed}echo \"$abcli_fullname seed for $target\"$delim_section"

    if [[ "$include_aws" == 1 ]]; then
        seed="$seed${sudo_prefix}rm -rf ~/.aws$delim"
        seed="$seed${sudo_prefix}mkdir ~/.aws$delim_section"
        seed="$seed$(bluer_ai_seed add_file $HOME/.aws/config \$HOME/.aws/config)$delim"
        seed="$seed$(bluer_ai_seed add_file $HOME/.aws/credentials \$HOME/.aws/credentials)$delim_section"
    fi

    # expected to append to/update $seed
    local function_name="bluer_ai_seed_${target}"
    if [[ $(type -t $function_name) == "function" ]]; then
        $function_name "$@"
    else
        bluer_ai_log_error "@seed: $target: target not found."
        return 1
    fi

    if [ ! -z "$env_name" ]; then
        seed="${seed}bluer_ai_env dot copy $env_name$delim"
        seed="${seed}bluer_ai init$delim_section"
    fi

    [[ "$do_eval" == 1 ]] &&
        seed="${seed}bluer_ai_eval ${@:3}$delim_section"

    if [ "$output" == "clipboard" ]; then
        if [ "$abcli_is_mac" == true ]; then
            echo $seed | pbcopy
        elif [ "$abcli_is_ubuntu" == true ]; then
            echo $seed | xclip -sel clip
        fi

        [[ "$do_log" == 1 ]] &&
            bluer_ai_log "📋 paste the seed 🌱 in the $target terminal."
    elif [ "$output" == "key" ] || [ "$output" == "filename" ]; then
        filename=$(bluer_ai_option "$options" filename $abcli_object_path/seed)
        [[ "$output" == "key" ]] &&
            filename="$seed_path/bluer_ai/$target"

        echo -en $seed >$filename.sh
        chmod +x $filename.sh

        echo "{\"version\":\"$bluer_ai_version\"}" >$filename.json

        [[ "$do_log" == 1 ]] &&
            bluer_ai_log "seed 🌱 -> $filename."
    elif [ "$output" == "screen" ]; then
        printf "$GREEN$seed$NC\n"
    else
        bluer_ai_log_error "this should not happen - output: $output".
        return 1
    fi
}
