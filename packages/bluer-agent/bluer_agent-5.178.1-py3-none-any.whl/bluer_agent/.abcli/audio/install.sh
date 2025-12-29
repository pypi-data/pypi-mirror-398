#! /usr/bin/env bash

function bluer_agent_audio_install() {
    if [[ "$abcli_is_rpi" == true ]]; then
        sudo apt install -y sox libsox-fmt-all libsox-fmt-alsa
        return
    fi

    if [[ "$abcli_is_mac" == true ]]; then
        brew install sox
        return
    fi

    bluer_ai_log_error "@agent: audio: install: do not know how to install."
    return 1
}
