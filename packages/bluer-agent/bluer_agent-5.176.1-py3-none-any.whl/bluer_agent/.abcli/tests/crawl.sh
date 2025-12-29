#! /usr/bin/env bash

function test_bluer_agent_crawl() {
    local options=$1

    local object_name=test_bluer_agent_crawl-$(bluer_ai_string_timestamp)
    local root=https://badkoobeh.com/

    bluer_ai_eval ,$options \
        bluer_agent_crawl \
        collect \
        root=$root \
        $object_name \
        --page-count 5 \
        --max-depth 2
    [[ $? -ne 0 ]] && return 1

    bluer_ai_hr

    bluer_ai_eval ,$options \
        bluer_agent_crawl \
        review \
        root=$root \
        $object_name
}
