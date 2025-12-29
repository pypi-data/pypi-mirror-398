#! /usr/bin/env bash

function bluer_ai_source_dependencies() {
    source $abcli_path_bash/bootstrap/paths.sh
    source $abcli_path_bash/bootstrap/system.sh
    source $abcli_path_bash/bootstrap/logging.sh

    local venv_path="$HOME/venv/bluer_ai/bin/activate"
    if [[ -f "$venv_path" ]]; then
        echo "🌀 sourcing $venv_path ..."
        source "$venv_path"
    fi

    [[ "$abcli_is_rpi" == true ]] &&
        export PATH="$HOME/.local/bin:$PATH"

    echo "🐍 $(python3 --version): $(which python)"
    echo "GNU bash $BASH_VERSION"

    python3 -m blueness version \
        --show_icon 1

    source $(python3 -m bluer_options locate)/.bash/bluer_options.sh

    local module_name
    for module_name in abcli modules plugins; do
        pushd $abcli_path_bash/$module_name >/dev/null

        if [ "$module_name" == "plugins" ]; then
            local plugins=($(ls *.sh))
            local plugins=${plugins[*]}
            local plugins=$(python3 -c "print('$plugins'.replace('.sh',''))")
            [[ "$abcli_is_in_notebook" == false ]] &&
                bluer_ai_log_list "$plugins" \
                    --before "loading" \
                    --delim space \
                    --after "plugin(s)"
        fi

        local filename
        for filename in *.sh; do
            source $filename
        done
        popd >/dev/null
    done

    bluer_ai_source_caller_suffix_path /../tests

    [[ "$abcli_is_in_notebook" == true ]] && return

    local repo_name
    for repo_name in $(bluer_ai_plugins list_of_external --log 0 --delim space --repo_names 1); do
        local module_name=$(bluer_ai_plugins get_module_name $repo_name)
        pushd $abcli_path_git/$repo_name/$module_name/.abcli >/dev/null

        local filename
        for filename in *.sh; do
            source $filename
        done
        popd >/dev/null
    done

    local list_of_installed_plugins=$(bluer_ai_plugins list_of_installed \
        --log 0 \
        --delim space)
    if [[ -z "$list_of_installed_plugins" ]]; then
        bluer_ai_log "🌀 no pip-installed plugins."
        return 0
    else
        bluer_ai_log_list "$list_of_installed_plugins" \
            --before "🌀 loading" \
            --delim space \
            --after "pip-installed plugin(s)"

        local paths_of_installed_plugins=$(bluer_ai_plugins list_of_installed \
            --log 0 \
            --delim space \
            --return_path 1)
        for module_path in $paths_of_installed_plugins; do
            #bluer_ai_log "🔵 $module_path"
            pushd $module_path >/dev/null

            local filename
            for filename in *.sh; do
                source $filename
            done
            popd >/dev/null
        done
    fi
}
