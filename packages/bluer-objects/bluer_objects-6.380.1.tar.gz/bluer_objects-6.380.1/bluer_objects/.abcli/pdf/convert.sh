#! /usr/bin/env bash

function bluer_objects_pdf_convert() {
    local options=$1
    local do_inline=$(bluer_ai_option_int "$options" inline 0)
    local do_install=$(bluer_ai_option_int "$options" install 0)
    local do_combine=$(bluer_ai_option_int "$options" combine 0)
    local do_compress=$(bluer_ai_option_int "$options" compress $do_combine)
    local do_upload=$(bluer_ai_option_int "$options" upload 0)
    local filename=$(bluer_ai_option "$options" filename release.pdf)

    if [[ "$do_install" == 1 ]]; then
        pip install pypandoc
        pip install PyPDF2

        if [[ "$abcli_is_mac" == true ]]; then
            brew install pandoc
            brew install wkhtmltopdf
            brew install ghostscript
        fi
    fi

    if [[ "$do_inline" == 1 ]]; then
        local module_name=${2:-object}
        if alias "$module_name" &>/dev/null; then
            module_name=$(alias "$module_name" | sed -E "s/^alias $module_name='(.*)'$/\1/")
        fi

        local path_prefix=$(python3 -m $module_name locate)/docs/

        local suffixes=${3:-metadata}

        local object_name=$(bluer_ai_clarify_object $4 pdf-$(bluer_ai_string_timestamp))

        bluer_ai_log "@pdf $module_name/$suffixes -> $object_name ..."

        bluer_ai_eval dryrun=$do_dryrun \
            python3 -m bluer_objects.pdf \
            convert \
            --path_prefix $path_prefix \
            --object_name $object_name \
            --suffixes $suffixes \
            --combine $do_combine \
            "${@:5}"
    else
        local object_name=$(bluer_ai_clarify_object $2 pdf-$(bluer_ai_string_timestamp))

        bluer_ai_log "@pdf $object_name ..."

        bluer_ai_eval dryrun=$do_dryrun \
            python3 -m bluer_objects.pdf \
            convert \
            --object_name $object_name \
            --combine $do_combine \
            --use_metadata 1 \
            "${@:3}"
    fi
    [[ $? -ne 0 ]] && return 1

    if [[ "$do_compress" == 1 ]]; then
        bluer_ai_log "compressing..."

        local object_path=$ABCLI_OBJECT_ROOT/$object_name
        mv -v \
            $object_path/$filename \
            $object_path/_$filename

        gs -sDEVICE=pdfwrite \
            -dCompatibilityLevel=1.4 \
            -dPDFSETTINGS=/ebook \
            -dNOPAUSE \
            -dBATCH \
            -sOutputFile=$object_path/$filename \
            $object_path/_$filename
        [[ $? -ne 0 ]] && return 1

        rm $object_path/_$filename
        bluer_ai_log "-> $object_path/$filename"
    fi

    if [[ "$do_upload" == 1 ]]; then
        bluer_objects_upload \
            filename=$filename \
            $object_name
        [[ $? -ne 0 ]] && return 1

        if [[ "$do_inline" == 0 ]]; then
            bluer_objects_metadata_upload \
                $object_name
        fi
    fi
}
