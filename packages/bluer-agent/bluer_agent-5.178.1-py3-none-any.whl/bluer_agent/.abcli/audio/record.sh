#! /usr/bin/env bash

function bluer_agent_audio_record() {
    local options=$1
    local filename=$(bluer_ai_option "$options" filename audio.wav)
    local do_upload=$(bluer_ai_option_int "$options" upload 0)
    local do_play=$(bluer_ai_option_int "$options" play 0)

    local object_name=$(bluer_ai_clarify_object $2 audio-$(bluer_ai_string_timestamp))

    python3 -m bluer_agent.audio \
        record \
        --object_name $object_name \
        --filename $filename \
        "${@:3}"
    [[ $? -ne 0 ]] && return 1

    [[ "$do_upload" == 1 ]] &&
        bluer_objects_upload \
            filename=$filename \
            $object_name

    if [[ "$do_play" == 1 ]]; then
        bluer_agent_audio_play \
            filename=$filename \
            $object_name
    fi
}
