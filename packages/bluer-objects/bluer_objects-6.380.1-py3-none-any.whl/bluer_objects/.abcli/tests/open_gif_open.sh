#! /usr/bin/env bash

function test_bluer_objects_gif_open() {
    local options=$1

    bluer_ai_eval ,$options \
        bluer_objects_gif \
        open \
        download \
        $BLUER_OBJECTS_TEST_OBJECT \
        "${@:2}"

    return 0
}
