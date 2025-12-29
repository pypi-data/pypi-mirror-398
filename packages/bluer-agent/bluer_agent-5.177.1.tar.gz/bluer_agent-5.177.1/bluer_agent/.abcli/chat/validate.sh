#! /usr/bin/env bash

function bluer_agent_chat_validate() {
    bluer_ai_eval - \
        python3 -m bluer_agent.chat \
        validate \
        "$@"
}
