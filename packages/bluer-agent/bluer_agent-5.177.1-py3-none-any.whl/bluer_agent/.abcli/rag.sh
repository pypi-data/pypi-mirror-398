#! /usr/bin/env bash

function bluer_agent_rag() {
    local task=$1

    local function_name=bluer_agent_rag_$task
    if [[ $(type -t $function_name) == "function" ]]; then
        $function_name "${@:2}"
        return
    fi

    python3 bluer_agent.rag "$@"
}

bluer_ai_source_caller_suffix_path /rag
