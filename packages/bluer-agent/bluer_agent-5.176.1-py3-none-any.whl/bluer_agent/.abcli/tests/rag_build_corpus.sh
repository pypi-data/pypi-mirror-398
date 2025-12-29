#! /usr/bin/env bash

function test_bluer_agent_rag_build_corpus() {
    local options=$1

    local object_name=test_bluer_agent_rag_build_corpus-$(bluer_ai_string_timestamp)

    bluer_ai_eval ,$options \
        bluer_agent_rag \
        build_corpus \
        download \
        $BLUER_AGENT_CRAWL_TEST_OBJECT \
        $object_name
}
