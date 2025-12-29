#! /usr/bin/env bash

function bluer_objects_host() {
    local task=$1
    local options=$2

    if [ $task == "get" ]; then
        python3 -m bluer_options.host \
            get \
            --keyword "$2" \
            "${@:3}"
        return
    fi

    if [[ "|reboot|shutdown|" == *"|$task|"* ]]; then
        local command_line
        [[ $task == "reboot" ]] &&
            command_line="sudo reboot"
        [[ $task == "shutdown" ]] &&
            command_line="sudo shutdown -h now"

        local rpi=$(bluer_ai_option_int "$options" rpi 0)
        if [[ "$rpi" == 1 ]]; then
            local machine_name=$3
            if [[ -z "$machine_name" ]]; then
                bluer_ai_log_error "machine_name not found."
                return 1
            fi

            ssh \
                pi@$machine_name.local \
                $command_line

            return
        fi

        bluer_ai_eval ,$options \
            $command_line

        return
    fi

    bluer_ai_log_error "@host: $task: command not found."
    return 1
}
