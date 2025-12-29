#! /usr/bin/env bash

function bluer_objects_file() {
    local options=$1
    local do_sudo=$(bluer_ai_option_int "$options" sudo 0)

    local task=$2

    local prefix=""
    [[ "$do_sudo" == 1 ]] &&
        prefix="sudo -E"

    local filename=$3

    $prefix $(which python) -m bluer_objects.file \
        "$task" \
        --filename "$filename" \
        "${@:4}"
}
