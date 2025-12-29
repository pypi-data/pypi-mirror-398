#! /usr/bin/env bash

function test_bluer_agent_audio_record() {
    [[ "$abcli_is_github_workflow" == true ]] &&
        return 0

    local object_name=test_bluer_agent_audio-$(bluer_ai_string_timestamp)
    for crop_silence in 0 1; do
        bluer_agent_audio \
            record \
            filename=listen.wav,play \
            $object_name \
            --crop_silence $crop_silence \
            --length 10
        [[ $? -ne 0 ]] && return 1

        bluer_ai_hr
    done
}
