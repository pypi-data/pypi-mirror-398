#! /usr/bin/env bash

function test_bluer_objects_storage_status() {
    local options=$1

    bluer_ai_storage_status
    [[ $? -ne 0 ]] && return 1
    bluer_ai_hr

    bluer_ai_storage_status \
        depth=2,count=10
}
