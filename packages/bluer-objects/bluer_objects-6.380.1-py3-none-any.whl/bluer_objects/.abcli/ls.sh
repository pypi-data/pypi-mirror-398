#! /usr/bin/env bash

function bluer_objects_ls() {
    local options=$1
    local where=$(bluer_ai_option_choice "$options" cloud,local)
    local objects=$(bluer_ai_option_int "$options" objects 0)

    if [[ "$objects" == 1 ]]; then
        python3 -m bluer_objects.storage \
            ls_objects \
            --where $where \
            "${@:2}"

        return
    fi

    if [[ -z "$where" ]]; then
        ls -1 "$@"
        return
    fi

    local object_name=$(bluer_ai_clarify_object $2 .)

    python3 -m bluer_objects.storage \
        ls \
        --object_name $object_name \
        --where $where \
        "${@:3}"
}
