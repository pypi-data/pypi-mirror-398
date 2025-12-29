#! /usr/bin/env bash

function test_file_asset() {
    echo $abcli_path_git/bluer-objects/bluer_objects/.abcli/tests/file.sh
}

function test_file_replace() {
    local options=$1

    local filename=$abcli_path_git/file.sh

    cp -v \
        $(test_file_asset) \
        $filename
    [[ $? -ne 0 ]] && return 1

    bluer_objects_file - \
        replace \
        $filename \
        --this function+local \
        --that FUNCTION+LOCAL \
        --cat 1 \
        "${@:2}"
    [[ $? -ne 0 ]] && return 1
    bluer_ai_hr

    # ---

    bluer_objects_file - \
        replace \
        $filename \
        --this "FUNCTION test_file_asset() {+echo" \
        --that ":)+:(" \
        --cat 1 \
        --whole_line 1 \
        "${@:2}"
    [[ $? -ne 0 ]] && return 1
    rm -v $filename
}

function test_file_size() {
    local options=$1

    local size=$(bluer_objects_file - \
        size \
        $(test_file_asset))

    bluer_ai_assert \
        "$size" \
        "1.18 kB"
    [[ $? -ne 0 ]] && return 1
    bluer_ai_hr

    # ---

    local size=$(bluer_objects_file - \
        size \
        $(test_file_asset) \
        --pretty 0)

    bluer_ai_assert \
        "$size" \
        "1209"
}
