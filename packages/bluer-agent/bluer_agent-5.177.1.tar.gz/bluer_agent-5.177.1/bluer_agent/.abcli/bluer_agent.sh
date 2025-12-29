#! /usr/bin/env bash

function bluer_agent() {
    local task=$1

    bluer_ai_generic_task \
        plugin=bluer_agent,task=$task \
        "${@:2}"
}

bluer_ai_log $(bluer_agent version --show_icon 1)
