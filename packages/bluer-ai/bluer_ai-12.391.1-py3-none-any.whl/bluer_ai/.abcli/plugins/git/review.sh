#! /usr/bin/env bash

function bluer_ai_git_review() {
    local repo_name=$(bluer_ai_git_get_repo_name)

    pushd $abcli_path_git/$repo_name >/dev/null

    local list_of_files=$(git diff --name-only HEAD | tr "\n" " ")
    local list_of_files=$(bluer_ai_list_nonempty "$list_of_files" --delim space)
    if [[ -z "$list_of_files" ]]; then
        bluer_ai_log_warning "@git: review: no changes."
        popd >/dev/null
        return
    fi

    local char="x"
    local index=0
    local count=$(bluer_ai_list_len "$list_of_files" --delim=space)
    while true; do
        local index=$(python3 -c "print(min($count-1,max(0,$index)))")
        local filename=$(bluer_ai_list_item "$list_of_files" $index --delim space)

        clear
        git status
        bluer_ai_hr
        printf "📜 $RED$filename$NC\n"

        if [[ "$filename" == *.ipynb ]]; then
            bluer_ai_log_warning "jupyter notebook, will not review."
        else
            git diff $filename
        fi

        bluer_ai_hr
        bluer_ai_log "# Enter|space: next - p: previous - q: quit."
        read -n 1 char
        [[ "$char" == "q" ]] && break
        [[ -z "$char" ]] && ((index++))
        [[ "$char" == "p" ]] && ((index--))

        $(python3 -c "print(str($index >= $count).lower())") && break
    done

    popd >/dev/null
}
