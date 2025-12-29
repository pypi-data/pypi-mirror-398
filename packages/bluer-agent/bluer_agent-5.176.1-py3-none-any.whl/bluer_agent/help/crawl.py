from typing import List

from bluer_options.terminal import show_usage, xtra

from bluer_agent.crawl.collect import CollectionProperties


def help_collect(
    tokens: List[str],
    mono: bool,
) -> str:
    options = "".join(
        [
            xtra("download,", mono=mono),
            "root=<url>|all",
            xtra(",upload", mono=mono),
        ]
    )

    properties = CollectionProperties()
    args = [
        "[--page-count 25]",
        "[--max-depth 2]",
        f"[--timeout {properties.timeout}]",
        f"[--max-retries {properties.max_retries}]",
        f"[--backoff-base {properties.backoff_base}]",
        f"[--backoff-jitter {properties.backoff_jitter}]",
        f"[--delay {properties.delay}]",
    ]

    return show_usage(
        [
            "@crawl",
            "collect",
            f"[{options}]",
            "[-|<object-name>]",
        ]
        + args,
        "crawl -> <object-name>.",
        mono=mono,
    )


def help_review(
    tokens: List[str],
    mono: bool,
) -> str:
    options = "".join(
        [
            xtra("download,", mono=mono),
            "root=<url>|all",
        ]
    )

    return show_usage(
        [
            "@crawl",
            "review",
            f"[{options}]",
            "[.|<object-name>]",
        ],
        "review <object-name>.",
        mono=mono,
    )


help_functions = {
    "collect": help_collect,
    "review": help_review,
}
