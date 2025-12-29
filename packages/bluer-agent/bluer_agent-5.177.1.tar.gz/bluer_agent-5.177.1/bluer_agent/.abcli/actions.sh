#! /usr/bin/env bash

function bluer_agent_action_git_before_push() {
    bluer_agent build_README
    [[ $? -ne 0 ]] && return 1

    [[ "$(bluer_ai_git get_branch)" != "main" ]] &&
        return 0

    bluer_agent pypi build
}
