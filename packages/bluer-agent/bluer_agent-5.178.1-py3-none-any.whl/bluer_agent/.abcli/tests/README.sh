#! /usr/bin/env bash

function test_bluer_agent_README() {
    local options=$1

    bluer_ai_eval ,$options \
        bluer_agent build_README
}
