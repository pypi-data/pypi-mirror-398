#! /usr/bin/env bash

function bluer_objects_assets_cd() {
    local options=$1
    local do_create=$(bluer_ai_option_int "$options" create 0)
    local volume=$(bluer_ai_option "$options" vol)

    local path=$2
    path=$abcli_path_git/assets$volume/$path

    if [[ "$do_create" == 1 ]]; then
        mkdir -pv $path
        [[ $? -ne 0 ]] && return 1
    fi

    cd $path
    [[ $? -ne 0 ]] && return 1

    bluer_ai_log "🔗 $path"
}
