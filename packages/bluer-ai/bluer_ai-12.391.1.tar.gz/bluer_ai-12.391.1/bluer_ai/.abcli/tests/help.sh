#! /usr/bin/env bash

function test_bluer_ai_help() {
    local options=$1

    local module
    for module in \
        \
        "@assert" \
        "@assert list" \
        \
        "@badge" \
        \
        "@browse" \
        \
        "@build_README" \
        \
        "@cat" \
        \
        "@code" \
        \
        "@conda" \
        "@conda create" \
        "@conda exists" \
        "@conda list" \
        "@conda rm" \
        \
        "@env" \
        "@env backup" \
        "@env backup list" \
        "@env dot" \
        "@env dot cat" \
        "@env dot cat" \
        "@env dot cp" \
        "@env dot edit" \
        "@env dot get" \
        "@env dot list" \
        "@env dot load" \
        "@env dot set" \
        \
        "@error" \
        \
        "@git" \
        "@git browse" \
        "@git checkout" \
        "@git clone" \
        "@git create_branch" \
        "@git create_pull_request" \
        "@git get_branch" \
        "@git get_remote" \
        "@git get_repo_name" \
        "@git increment_version" \
        "@git pull" \
        "@git push" \
        "@git recreate_ssh" \
        "@git reset" \
        "@git review" \
        "@git rm" \
        "@git seed" \
        "@git set_remote" \
        "@git status" \
        "@git sync_fork" \
        \
        "@gpu" \
        "@gpu status" \
        "@gpu status get" \
        "@gpu status show" \
        "@gpu validate" \
        \
        "@help" \
        \
        "@hr" \
        \
        "@init" \
        \
        "@latex" \
        "@latex bibclean" \
        "@latex build" \
        "@latex install" \
        \
        "@list" \
        "@list filter" \
        "@list in" \
        "@list intersect " \
        "@list item" \
        "@list len " \
        "@list log " \
        "@list next" \
        "@list nonempty" \
        "@list prev" \
        "@list resize" \
        "@list reverse" \
        "@list sort" \
        \
        "@log" \
        "@log rm" \
        "@log verbose" \
        "@log watch" \
        "@log::list" \
        \
        "@not" \
        \
        "@open" \
        \
        "@option" \
        "@option::choice" \
        "@option::int" \
        \
        "@pause" \
        \
        "@perform_action" \
        \
        "@plugins get_module_name" \
        "@plugins install" \
        "@plugins list_of_external" \
        "@plugins list_of_installed" \
        "@plugins transform" \
        \
        "@pylint" \
        \
        "@pypi" \
        "@pypi browse" \
        "@pypi build" \
        "@pypi install" \
        \
        "@pytest" \
        \
        "@random" \
        \
        "@repeat" \
        \
        "@screen" \
        "@screen detach" \
        "@screen list" \
        "@screen resume" \
        \
        "@seed" \
        "@seed eject" \
        "@seed list" \
        \
        "@select" \
        \
        "@session" \
        "@session start" \
        \
        "@sleep" \
        \
        "@ssh" \
        "@ssh add" \
        "@ssh copy_id" \
        "@ssh ec2" \
        "@ssh sbc" \
        "@ssh keygen" \
        \
        "@test" \
        "@test list" \
        \
        "@terraform" \
        "@terraform cat" \
        "@terraform disable" \
        "@terraform enable" \
        "@terraform get" \
        \
        "@timestamp" \
        "@@timestamp" \
        \
        "@today" \
        \
        "@warn" \
        \
        "@watch" \
        \
        "@wifi" \
        "@wifi diagnose" \
        "@wifi get_ssid" \
        \
        "bluer_ai_log_list" \
        "bluer_ai_source_caller_suffix_path" \
        "bluer_ai_source_path" \
        \
        "bluer_ai_string_after" \
        "bluer_ai_string_before" \
        \
        "bluer_ai"; do
        bluer_ai_eval ,$options \
            bluer_ai_help $module
        [[ $? -ne 0 ]] && return 1

        bluer_ai_hr
    done

    return 0
}
