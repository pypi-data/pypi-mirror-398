#! /usr/bin/env bash

function bluer_agent_voice_generate() {
  local options=$1
  local do_play=$(bluer_ai_option_int "$options" play 1)
  local do_download=$(bluer_ai_option_int "$options" download $do_play)
  local filename=$(bluer_ai_option "$options" filename voice-$(bluer_ai_string_timestamp).mp3)

  local object_name=$(bluer_ai_clarify_object $2 voice-$(bluer_ai_string_timestamp))

  local sentence=${3:-void}

  python3 -m bluer_agent.voice \
    generate \
    --sentence "$sentence" \
    --download $do_download \
    --object_name $object_name \
    --filename $filename \
    "${@:4}"
  [[ $? -ne 0 ]] && return 1

  [[ "$do_play" == 0 ]] &&
    return

  bluer_agent_audio \
    play \
    filename=$filename \
    $object_name
}
