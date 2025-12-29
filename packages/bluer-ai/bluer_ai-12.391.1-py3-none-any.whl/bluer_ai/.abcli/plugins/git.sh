#! /usr/bin/env bash

function bluer_ai_git() {
    local task=$1
    [[ "$task" == "increment" ]] && task="increment_version"
    [[ "$task" == "++" ]] && task="increment_version"

    if [ "$task" == "seed" ]; then
        bluer_ai_seed git "${@:2}"
        return
    fi

    local repo_name=$(bluer_ai_unpack_repo_name $1)
    if [ -d "$abcli_path_git/$repo_name" ]; then
        if [[ -z "${@:2}" ]]; then
            cd $abcli_path_git/$repo_name
            return
        fi

        pushd $abcli_path_git/$repo_name >/dev/null
        bluer_ai_git "${@:2}"
        local status="$?"
        popd >/dev/null

        return $status
    fi

    local function_name="bluer_ai_git_$task"
    if [[ $(type -t $function_name) == "function" ]]; then
        $function_name "${@:2}"
        return
    fi

    local repo_name=$(bluer_ai_git_get_repo_name)
    if [[ "$repo_name" == "unknown" ]]; then
        bluer_ai_log_error "@git: $task: $(pwd): repo not found."
        return 1
    fi

    if [[ "$task" == "create_pull_request" ]]; then
        bluer_ai_browse \
            https://github.com/kamangir/$repo_name/compare/$(bluer_ai_git get_branch)?expand=1
        return
    fi

    if [[ "$task" == "get_branch" ]]; then
        # https://stackoverflow.com/a/1593487
        local branch_name="$(git symbolic-ref HEAD 2>/dev/null)" ||
            branch_name="master" # detached HEAD

        echo ${branch_name##refs/heads/}
        return
    fi

    if [ "$task" == "recreate_ssh" ]; then
        # https://www.cyberciti.biz/faq/sudo-append-data-text-to-file-on-linux-unix-macos/
        ssh-keyscan github.com | sudo tee -a ~/.ssh/known_hosts
        sudo ssh -T git@github.com
        return
    fi

    if [ "$task" == "reset" ]; then
        bluer_ai_eval - "git reset --hard @{u}"
        return
    fi

    if [ "$task" == "sync_fork" ]; then
        local branch_name=$2

        # https://stackoverflow.com/a/7244456/17619982
        cd $abcli_path_git/$repo_name
        git fetch upstream
        git checkout $branch_name
        git rebase upstream/$branch_name
        return
    fi

    git "$@"
}

bluer_ai_source_caller_suffix_path /git

bluer_ai_refresh_branch_and_version
