from blueness import module
from bluer_options import string
from bluer_options.host import is_rpi
from bluer_objects import file, objects
from bluer_objects.host import shell

from bluer_agent import NAME
from bluer_agent.logger import logger


NAME = module.name(__file__, NAME)


def play(
    object_name: str,
    filename: str = "audio.wav",
) -> bool:
    full_filename = objects.path_of(
        object_name=object_name,
        filename=filename,
    )
    if not file.exists(full_filename):
        logger.error(f"file not found: {full_filename}")
        return False

    logger.info(
        "{}.play: {}/{} ({})".format(
            NAME,
            object_name,
            filename,
            string.pretty_bytes(file.size(full_filename)),
        )
    )

    command = (
        (
            "ffmpeg -i {} -f wav - | aplay"
            if file.extension(filename) == "mp3"
            else "aplay {}"
        )
        if is_rpi()
        else "afplay {}"
    )

    return shell(
        command=command.format(full_filename),
        log=True,
    )


""
