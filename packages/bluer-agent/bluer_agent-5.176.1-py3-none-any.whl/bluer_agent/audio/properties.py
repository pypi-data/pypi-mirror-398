from typing import List
import argparse

from bluer_options import string
from bluer_options.host import is_rpi

from bluer_agent.audio import env


class AudioProperties:
    def __init__(
        self,
        channels: int = 1,
        crop_silence: bool = True,
        length: int = 30,  # in seconds
        rate: int = 48000,
    ):
        self.channels: int = channels
        self.crop_silence: bool = crop_silence
        self.length: int = length
        self.rate: int = rate

    @staticmethod
    def add_args(parser: argparse.ArgumentParser):
        parser.add_argument(
            "--channels",
            type=int,
            default=1,
        )
        parser.add_argument(
            "--crop_silence",
            type=int,
            default=1,
            help="0 | 1",
        )
        parser.add_argument(
            "--length",
            type=int,
            default=30,
            help="in seconds",
        )
        parser.add_argument(
            "--rate",
            type=int,
            default=48000,
        )

    def as_str(self):
        return "length<{}, sample rate:{}, {} channel(s){}".format(
            string.pretty_duration(self.length),
            self.rate,
            self.channels,
            ", crop silence" if self.crop_silence else "",
        )

    def record_command(
        self,
        filename: str,
    ) -> List[str]:
        # input device:
        # - On Raspberry Pi with mic as default: don't specify device
        # - If you need a specific ALSA device: add `-t alsa hw:1,0` after rec
        return (
            (
                [
                    "sudo",
                    "-u",
                    "pi",
                    "-H",
                ]
                if is_rpi()
                else []
            )
            + [
                "sox" if is_rpi() else "rec",
                "-V1",
            ]
            + (
                [
                    "-t",
                    "alsa",
                    '"plughw:CARD=C930e,DEV=0"',
                ]
                if is_rpi()
                else []
            )
            + [
                f'-r "{self.rate}"',
                f'-c "{self.channels}"',
                filename,
                f"trim 0 {self.length}",
            ]
            + (
                [
                    "silence",
                    f'1 "{env.BLUER_AGENT_AUDIO_LISTEN_START_HOLD}" "{env.BLUER_AGENT_AUDIO_LISTEN_START_THRESHOLD}"',
                    f'1 "{env.BLUER_AGENT_AUDIO_LISTEN_STOP_HOLD}" "{env.BLUER_AGENT_AUDIO_LISTEN_STOP_THRESHOLD}"',
                ]
                if self.crop_silence
                else []
            )
        )
