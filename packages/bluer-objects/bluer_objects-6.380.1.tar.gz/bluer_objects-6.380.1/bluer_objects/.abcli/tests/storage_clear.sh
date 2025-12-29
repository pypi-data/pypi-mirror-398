#! /usr/bin/env bash

function test_bluer_objects_storage_clear() {
    local options=$1

    bluer_ai_storage_clear cloud
    [[ $? -ne 0 ]] && return 1
    bluer_ai_hr

    bluer_ai_storage_clear cloud,public
}
