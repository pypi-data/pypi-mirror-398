#! /usr/bin/env bash

function bluer_objects_assets_mv() {
    local options=$1
    local do_create=$(bluer_ai_option_int "$options" create 0)
    local extension=$(bluer_ai_option "$options" extension jpg)
    local volume=$(bluer_ai_option "$options" vol)

    local path=$2
    path=$abcli_path_git/assets$volume/$path

    if [[ "$do_create" == 1 ]]; then
        mkdir -pv $path
        [[ $? -ne 0 ]] && return 1
    fi

    bluer_ai_log "Downloads/.$extension -> assets$volume/path"

    mv -v \
        $HOME/Downloads/*.$extension \
        $path
    [[ $? -ne 0 ]] && return 1

    local push_options=$3
    local do_push=$(bluer_ai_option_int "$push_options" push 0)
    [[ "$do_push" == 0 ]] &&
        return 0

    bluer_ai_git \
        assets$volume \
        push \
        "$path += " \
        $push_options
}
