#! /usr/bin/env bash

function test_bluer_agent_help() {
    local options=$1

    local module
    for module in \
        "@agent" \
        "@agent chat" \
        \
        "@agent chat validate" \
        "@agent transcribe" \
        \
        "@agent pypi" \
        "@agent pypi browse" \
        "@agent pypi build" \
        "@agent pypi install" \
        \
        "@agent pytest" \
        \
        "@agent test" \
        "@agent test list" \
        \
        "@ai_agent" \
        \
        "@audio" \
        "@audio install" \
        "@audio play" \
        "@audio record" \
        "@audio test" \
        \
        "@crawl" \
        "@crawl collect" \
        "@crawl review" \
        \
        "@rag" \
        "@rag build_corpus" \
        "@rag query" \
        \
        "@voice" \
        "@voice generate" \
        \
        "bluer_agent"; do
        bluer_ai_eval ,$options \
            bluer_ai_help $module
        [[ $? -ne 0 ]] && return 1

        bluer_ai_hr
    done

    return 0
}
