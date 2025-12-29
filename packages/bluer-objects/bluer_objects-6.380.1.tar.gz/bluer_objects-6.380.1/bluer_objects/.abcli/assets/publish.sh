#! /usr/bin/env bash

function bluer_objects_assets_publish() {
    local options=$1

    local do_download=$(bluer_ai_option_int "$options" download 0)
    local do_pull=$(bluer_ai_option_int "$options" pull 1)
    local do_push=$(bluer_ai_option_int "$options" push 0)
    local extensions=$(bluer_ai_option "$options" extensions png)

    [[ "$do_pull" == 1 ]] &&
        bluer_ai_git \
            assets \
            pull \
            ~all

    local object_name=$(bluer_ai_clarify_object $2 .)

    [[ "$do_download" == 1 ]] &&
        bluer_objects_download - $object_name

    bluer_ai_eval dryrun=$do_dryrun \
        python3 -m bluer_objects.assets \
        publish \
        --object_name $object_name \
        --extensions $extensions \
        "${@:3}"
    [[ $? -ne 0 ]] && return 1

    [[ "$do_push" == 1 ]] &&
        bluer_ai_git \
            assets \
            push \
            "$object_name update."

    return 0
}
