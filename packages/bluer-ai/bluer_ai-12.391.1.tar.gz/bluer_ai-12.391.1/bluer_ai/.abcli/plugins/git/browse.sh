#! /usr/bin/env bash

function bluer_ai_git_browse() {
    local repo_name=$1

    local options=$2
    local browse_actions=$(bluer_ai_option_int "$options" actions 0)

    if [[ ",,.,-," == *",$repo_name,"* ]]; then
        repo_name=$(bluer_ai_git_get_repo_name)
    else
        repo_name=$(bluer_ai_unpack_repo_name $repo_name)
    fi

    local url=https://github.com/kamangir/$repo_name
    [[ "$browse_actions" == 1 ]] && url="$url/actions"

    bluer_ai_browse $url
}
