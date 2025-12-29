#! /usr/bin/env bash

function test_bluer_agent_audio_play() {
    [[ "$abcli_is_github_workflow" == true ]] &&
        return 0

    bluer_agent_audio \
        play \
        download,filename=farsi.wav \
        $BLUER_AGENT_TRANSCRIPTION_TEST_OBJECT
}
