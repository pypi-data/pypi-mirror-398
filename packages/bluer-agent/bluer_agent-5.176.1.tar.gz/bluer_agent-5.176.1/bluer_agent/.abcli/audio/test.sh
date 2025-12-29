#! /usr/bin/env bash

function bluer_agent_audio_test() {
    bluer_ai_eval ,$options \
        speaker-test -t sine -l 1
}
