#! /usr/bin/env bash

function test_bluer_agent_crawl_all() {
    local options=$1

    local object_name=test_bluer_agent_crawl-$(bluer_ai_string_timestamp)

    local object_path=$ABCLI_OBJECT_ROOT/$object_name
    mkdir -pv $object_path

    cat >$object_path/metadata.yaml <<'EOF'
    corpus:
    - https://badkoobeh.com/
    - https://irannovin.net/
    - https://korosheh.com
EOF

    bluer_ai_eval ,$options \
        bluer_agent_crawl \
        collect \
        - \
        $object_name \
        --page-count 5 \
        --max-depth 2
    [[ $? -ne 0 ]] && return 1

    bluer_ai_hr

    bluer_ai_eval ,$options \
        bluer_agent_crawl \
        review \
        - \
        $object_name
}
