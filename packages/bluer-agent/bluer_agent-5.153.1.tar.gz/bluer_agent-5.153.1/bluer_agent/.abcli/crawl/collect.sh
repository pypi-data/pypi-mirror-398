#! /usr/bin/env bash

function bluer_agent_crawl_collect() {
    local options=$1
    local do_dryrun=$(bluer_ai_option_int "$options" dryrun 0)
    local do_download=$(bluer_ai_option_int "$options" download 0)
    local do_upload=$(bluer_ai_option_int "$options" upload 0)
    local root=$(bluer_ai_option "$options" root all)

    local object_name=$(bluer_ai_clarify_object $2 .)

    [[ "$do_download" == 1 ]] &&
        bluer_objects_download - $object_name

    bluer_ai_eval dryrun=$do_dryrun \
        python3 -m bluer_agent.crawl \
        collect \
        --root $root \
        --object_name $object_name \
        --out auto \
        "${@:3}"
    local status="$?"

    [[ "$do_upload" == 1 ]] &&
        bluer_objects_upload - $object_name

    return $status
}
