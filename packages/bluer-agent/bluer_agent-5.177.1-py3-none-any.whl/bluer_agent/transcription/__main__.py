import argparse

from blueness import module
from blueness.argparse.generic import sys_exit

from bluer_agent import NAME
from bluer_agent.transcription.functions import transcribe
from bluer_agent.audio.properties import AudioProperties
from bluer_agent.logger import logger

NAME = module.name(__file__, NAME)

parser = argparse.ArgumentParser(NAME)
parser.add_argument(
    "task",
    type=str,
    help="transcribe",
)
parser.add_argument(
    "--object_name",
    type=str,
)
parser.add_argument(
    "--filename",
    type=str,
)
parser.add_argument(
    "--language",
    type=str,
    default="fa",
    help="en | fa",
)
parser.add_argument(
    "--record",
    type=int,
    default=1,
    help="0 | 1",
)

AudioProperties.add_args(parser)

args = parser.parse_args()

success = False
if args.task == "transcribe":
    success, _ = transcribe(
        object_name=args.object_name,
        filename=args.filename,
        language=args.language,
        record=args.record,
        properties=AudioProperties(
            channels=args.channels,
            crop_silence=args.crop_silence == 1,
            length=args.length,
            rate=args.rate,
        ),
        post_metadata=True,
    )
else:
    success = None

sys_exit(logger, NAME, args.task, success)
