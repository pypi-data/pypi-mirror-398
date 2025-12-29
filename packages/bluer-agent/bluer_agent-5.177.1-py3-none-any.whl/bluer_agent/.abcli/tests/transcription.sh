#! /usr/bin/env bash

function test_bluer_agent_transcribe() {
    local options=$1
    local what=$(bluer_ai_option "$options" what record,farsi,english)

    bluer_ai_log "testing $what..."

    local do_play=0
    [[ "$abcli_is_github_workflow" == false ]] &&
        do_play=1

    if [[ "$abcli_is_github_workflow" == false ]] &&
        [[ ",$what," == *",record,"* ]]; then
        bluer_ai_eval ,$options \
            bluer_agent_transcribe \
            filename=farsi.wav,language=fa,play=$do_play \
            $object_name \
            --length 10
        [[ $? -ne 0 ]] && return 1

        bluer_ai_hr
    fi

    if [[ ",$what," == *",farsi,"* ]]; then
        bluer_ai_eval ,$options \
            bluer_agent_transcribe \
            download,filename=farsi.wav,language=fa,play=$do_play \
            $BLUER_AGENT_TRANSCRIPTION_TEST_OBJECT
        [[ $? -ne 0 ]] && return 1

        bluer_ai_hr
    fi

    if [[ ",$what," == *",english,"* ]]; then
        bluer_ai_eval ,$options \
            bluer_agent_transcribe \
            download,filename=english.wav,language=en,play=$do_play \
            $BLUER_AGENT_TRANSCRIPTION_TEST_OBJECT
    fi
}
