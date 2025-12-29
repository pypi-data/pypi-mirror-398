from typing import List

from bluer_options.terminal import show_usage, xtra

from bluer_agent.voice.functions import list_of_speakers


def help_generate(
    tokens: List[str],
    mono: bool,
) -> str:
    options = xtra("~download,~play", mono=mono)

    args = [
        "[--speaker {}]".format(" | ".join(list_of_speakers)),
        "[--speed < >0 >]",
        "[--timestamp 1]",
    ]

    return show_usage(
        [
            "@voice",
            "generate",
            f"[{options}]",
            "[-|<object-name>]",
            '"<sentence>"',
        ]
        + args,
        "generate voice.",
        mono=mono,
    )


help_functions = {
    "generate": help_generate,
}
