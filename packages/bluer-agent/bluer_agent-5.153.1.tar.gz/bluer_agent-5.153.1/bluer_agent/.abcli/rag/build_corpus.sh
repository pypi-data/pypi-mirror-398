#! /usr/bin/env bash

function bluer_agent_rag_build_corpus() {
    local options=$1
    local do_dryrun=$(bluer_ai_option_int "$options" dryrun 0)
    local do_download=$(bluer_ai_option_int "$options" download 0)
    local do_upload=$(bluer_ai_option_int "$options" upload 0)

    local crawl_object_name=$(bluer_ai_clarify_object $2 .)

    local corpus_object_name=$(bluer_ai_clarify_object $3 corpus-$(bluer_ai_string_timestamp))

    [[ "$do_download" == 1 ]] &&
        bluer_objects_download - $crawl_object_name

    bluer_ai_eval dryrun=$do_dryrun \
        python3 -m bluer_agent.rag.corpus \
        build_and_embed \
        --crawl_object_name $crawl_object_name \
        --corpus_object_name $corpus_object_name \
        "${@:4}"
    local status="$?"

    [[ "$do_upload" == 1 ]] &&
        bluer_objects_upload - $corpus_object_name

    return $status
}
