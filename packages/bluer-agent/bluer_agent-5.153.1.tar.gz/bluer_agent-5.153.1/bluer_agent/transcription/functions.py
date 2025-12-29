from typing import Tuple
import json

from blueness import module
from bluer_options import string
from bluer_objects import file, objects
from bluer_objects.host import shell
from bluer_objects.metadata import post_to_object

from bluer_agent import NAME
from bluer_agent import env
from bluer_agent.audio.properties import AudioProperties
from bluer_agent.audio.record import record as record_audio
from bluer_agent.logger import logger


NAME = module.name(__file__, NAME)


def transcribe(
    object_name: str,
    filename: str = "",
    language: str = "fa",
    record: bool = False,
    properties: AudioProperties = AudioProperties(),
    post_metadata: bool = False,
) -> Tuple[bool, str]:
    if not filename:
        filename = "{}.wav".format(string.timestamp())

    if record and not record_audio(
        object_name=object_name,
        filename=filename,
        properties=properties,
    ):
        return False, ""

    logger.info(
        "{}.transcribe({}/{}) [{}]".format(
            NAME,
            object_name,
            file.name_and_extension(filename),
            language,
        )
    )

    # https://docs.arvancloud.ir/fa/aiaas/api-usage
    attempt = 1
    success: bool = False
    text: str = ""
    while attempt <= env.BLUER_AGENT_TRANSCRIPTION_RETRIAL:
        if attempt >= 2:
            logger.info(
                f"attempt {attempt} / {env.BLUER_AGENT_TRANSCRIPTION_RETRIAL}..."
            )

        command = [
            "curl",
            "--fail",
            f'--location "{env.BLUER_AGENT_TRANSCRIPTION_ENDPOINT}/audio/transcriptions"',
            f'--header "Authorization: apikey {env.BLUER_AGENT_API_KEY}"',
            f'--form "model={env.BLUER_AGENT_TRANSCRIPTION_MODEL_NAME}"',
            '--form "file=@{}"'.format(
                objects.path_of(
                    object_name=object_name,
                    filename=filename,
                )
            ),
            f'--form "language={language}"',
        ]

        success, output = shell(
            command,
            return_output=True,
            clean_after=True,
        )
        if success:
            if not output:
                logger.warning("silence detected.")
                text = ""
                break

            try:
                output_dict = json.loads(" ".join(output))

                assert isinstance(
                    output_dict, dict
                ), f"dict expected, received {output_dict.__class__.__name__}"

                assert "text" in output_dict, f'"text" not found in {output_dict}'

                text = output_dict["text"]

                break
            except Exception as e:
                logger.warning(f"bad output: {output}")
                logger.warning(e)

        logger.warning(f"transcription failed (attempt {attempt}).")
        attempt += 1

    if not success:
        logger.error(
            f"reached maximum retry limit ({env.BLUER_AGENT_TRANSCRIPTION_RETRIAL})."
        )
        return False, ""

    logger.info(text)

    return (
        not post_metadata
        or post_to_object(
            object_name,
            file.name(filename),
            text,
        ),
        text,
    )
