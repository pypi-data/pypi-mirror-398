from blueness import module

from bluer_options import string
from bluer_objects import file, objects
from bluer_objects.host import shell

from bluer_agent import NAME
from bluer_agent.audio.properties import AudioProperties
from bluer_agent.logger import logger


NAME = module.name(__file__, NAME)


def record(
    object_name: str,
    filename: str = "audio.wav",
    properties: AudioProperties = AudioProperties(),
) -> bool:
    full_filename = objects.path_of(
        object_name=object_name,
        filename=filename,
    )

    logger.info(
        "{}.record: {}/{} @ {} ... (^C to end)".format(
            NAME,
            object_name,
            filename,
            properties.as_str(),
        )
    )

    if not shell(
        command=properties.record_command(full_filename),
        log=True,
    ):
        return False

    if not file.exists(full_filename):
        logger.error(f"{full_filename} was not created.")
        return False

    logger.info(
        "audio size: {}".format(
            string.pretty_bytes(file.size(full_filename)),
        )
    )
    return True
