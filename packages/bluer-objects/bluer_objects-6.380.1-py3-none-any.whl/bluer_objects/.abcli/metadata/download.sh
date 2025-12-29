#! /usr/bin/env bash

function bluer_objects_metadata_download() {
    local object_name=$(bluer_ai_clarify_object $1 .)

    bluer_objects_download \
        filename=metadata.yaml \
        $object_name
}
