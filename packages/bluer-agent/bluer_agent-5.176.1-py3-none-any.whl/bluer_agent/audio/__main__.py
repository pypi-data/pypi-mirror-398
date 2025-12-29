import argparse

from blueness import module
from blueness.argparse.generic import sys_exit

from bluer_agent import NAME
from bluer_agent.audio.play import play
from bluer_agent.audio.record import record
from bluer_agent.audio.properties import AudioProperties
from bluer_agent.logger import logger

NAME = module.name(__file__, NAME)

parser = argparse.ArgumentParser(NAME)
parser.add_argument(
    "task",
    type=str,
    help="play | record",
)
parser.add_argument(
    "--object_name",
    type=str,
)
parser.add_argument(
    "--filename",
    type=str,
    default="audio.wav",
)

AudioProperties.add_args(parser)

args = parser.parse_args()

success = False
if args.task == "play":
    success = play(
        object_name=args.object_name,
        filename=args.filename,
    )
elif args.task == "record":
    success = record(
        object_name=args.object_name,
        filename=args.filename,
        properties=AudioProperties(
            channels=args.channels,
            crop_silence=args.crop_silence == 1,
            length=args.length,
            rate=args.rate,
        ),
    )
else:
    success = None

sys_exit(logger, NAME, args.task, success)
