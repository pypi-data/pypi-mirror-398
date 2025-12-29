#! /usr/bin/env bash

function bluer_objects_metadata_edit() {
    local options=$1
    local do_download=$(bluer_ai_option_int "$options" download 0)

    local object_name=$(bluer_ai_clarify_object $2 .)

    if [[ "$do_download" == 1 ]]; then
        bluer_objects_metadata_download \
            $object_name
    fi

    bluer_ai_code $ABCLI_OBJECT_ROOT/$object_name/metadata.yaml
}
