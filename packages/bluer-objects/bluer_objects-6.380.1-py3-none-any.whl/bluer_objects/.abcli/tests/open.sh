#! /usr/bin/env bash

function test_bluer_objects_open() {
    local options=$1

    bluer_ai_eval ,$options \
        bluer_ai_open \
        ,$options \
        $BLUER_OBJECTS_TEST_OBJECT \
        "${@:2}"
}
