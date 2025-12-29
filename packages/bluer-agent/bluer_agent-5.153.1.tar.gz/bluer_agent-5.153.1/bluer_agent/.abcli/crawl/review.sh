#! /usr/bin/env bash

function bluer_agent_crawl_review() {
    local options=$1
    local do_dryrun=$(bluer_ai_option_int "$options" dryrun 0)
    local do_download=$(bluer_ai_option_int "$options" download 1)
    local root=$(bluer_ai_option "$options" root all)

    local object_name=$(bluer_ai_clarify_object $2 .)

    [[ "$do_download" == 1 ]] &&
        bluer_objects_download - $object_name

    bluer_ai_eval dryrun=$do_dryrun \
        python3 -m bluer_agent.crawl \
        review \
        --object_name $object_name \
        --root $root \
        "${@:3}"
}
