#! /usr/bin/env bash

function bluer_agent_transcribe() {
    local options=$1
    local do_install=$(bluer_ai_option_int "$options" install 0)
    local do_download=$(bluer_ai_option_int "$options" download 0)
    local do_play=$(bluer_ai_option_int "$options" play 0)
    local do_upload=$(bluer_ai_option_int "$options" upload 0)
    local filename=$(bluer_ai_option "$options" filename audio-$(bluer_ai_string_timestamp).wav)

    if [[ "$do_install" == 1 ]]; then
        bluer_agent_audio_install
        [[ $? -ne 0 ]] && return 1
    fi

    local object_name=$(bluer_ai_clarify_object $2 transcription-$(bluer_ai_string_timestamp))

    [[ "$do_download" == 1 ]] &&
        bluer_objects_download \
            filename=$filename \
            $object_name

    bluer_ai_eval - \
        python3 -m bluer_agent.transcription \
        transcribe \
        --object_name $object_name \
        --filename $filename \
        --record $(bluer_ai_not $do_download) \
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
