#! /usr/bin/env bash

function bluer_objects_pdf() {
    local task=$1

    local function_name=bluer_objects_pdf_$task
    if [[ $(type -t $function_name) == "function" ]]; then
        $function_name "${@:2}"
        return
    fi

    python3 bluer_objects.pdf "$@"
}

bluer_ai_source_caller_suffix_path /pdf
