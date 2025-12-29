from typing import List

from bluer_options.terminal import show_usage, xtra

from bluer_agent.help.audio import record_args


def help(
    tokens: List[str],
    mono: bool,
) -> str:
    options = "".join(
        [
            xtra("download,filename=<filename.wav>,install,", mono=mono),
            "play",
            xtra(",upload", mono=mono),
        ]
    )

    args = sorted(
        [
            "[--language en|fa]",
            "[--record 0]",
        ]
        + record_args
    )

    return show_usage(
        [
            "@transcribe",
            f"[{options}]",
            "[-|<object-name>]",
        ]
        + args,
        "validate transcription.",
        mono=mono,
    )
