#! /usr/bin/env bash

function bluer_agent_audio_play() {
    local options=$1
    local do_download=$(bluer_ai_option_int "$options" download 0)
    local filename=$(bluer_ai_option "$options" filename audio.wav)

    local object_name=$(bluer_ai_clarify_object $2 .)

    [[ "$do_download" == 1 ]] &&
        bluer_objects_download \
            filename=$filename \
            $object_name

    python3 -m bluer_agent.audio \
        play \
        --object_name $object_name \
        --filename $filename \
        "${@:3}"
}
