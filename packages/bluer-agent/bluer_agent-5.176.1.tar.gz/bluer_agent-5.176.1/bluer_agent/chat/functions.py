from typing import List, Dict, Tuple
import requests
import re

from blueness import module
from bluer_options.logger.config import log_list

from bluer_agent import NAME
from bluer_agent import env
from bluer_agent.logger import logger


NAME = module.name(__file__, NAME)


def chat(
    messages: List[Dict],
    remove_thoughts: bool = True,
) -> Tuple[bool, str]:
    log_list(
        logger,
        f"{NAME}.chat({env.BLUER_AGENT_CHAT_MODEL_NAME}):",
        [str(message) for message in messages],
        "message(s)",
    )

    headers = {
        "Authorization": f"apikey {env.BLUER_AGENT_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": env.BLUER_AGENT_CHAT_MODEL_NAME,
        "messages": messages,
        "max_tokens": env.BLUER_AGENT_CHAT_MAX_TOKENS,
        "temperature": env.BLUER_AGENT_CHAT_TEMPERATURE,
    }

    try:
        response = requests.post(
            "{}/chat/completions".format(env.BLUER_AGENT_CHAT_ENDPOINT),
            headers=headers,
            json=payload,
            timeout=env.BLUER_AGENT_CHAT_TIMEOUT,
        )
    except Exception as e:
        logger.error(f"failed to send request: {e}")
        return False, ""

    success = True
    response_json = {}
    if response.status_code // 100 != 2:  # Check if status code is not in the 2xx range
        logger.info(
            "failed, status_code: {}, reason: {}.".format(
                response.status_code,
                response.reason,
            )
        )
        success = False
    else:
        try:
            response_json = response.json()
        except Exception as e:
            logger.error(f"failed to parse response to json: {e}, response: {response}")
            success = False

    if success:
        if not isinstance(response_json, dict):
            logger.error("response is not a dict")
            success = False
        elif "choices" not in response_json:
            logger.error("choices not in response")
            success = False
        elif len(response_json["choices"]) == 0:
            logger.error("response.choices is empty")
            success = False
        elif len(response_json["choices"]) > 1:
            logger.warning(
                "{} choice(s), will use the first one.".format(response_json["choices"])
            )
    if not success:
        return success, ""

    text = response_json["choices"][0].get("message", {}).get("content", "")

    if remove_thoughts and text:
        text = re.sub(
            r"<think>.*?</think>",
            "",
            text,
            flags=re.DOTALL | re.IGNORECASE,
        )

    text = re.sub(r"\s+", " ", text).strip()

    logger.info(text)

    return success, text
