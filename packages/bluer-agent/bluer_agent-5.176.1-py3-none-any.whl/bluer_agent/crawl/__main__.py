import argparse
from tqdm import tqdm
from typing import List

from blueness import module
from blueness.argparse.generic import sys_exit
from bluer_options.logger.config import log_list
from bluer_objects import objects
from bluer_objects.file import list_of
from bluer_objects.file import name as file_name
from bluer_objects.metadata import get_from_object

from bluer_agent import NAME
from bluer_agent.crawl import file
from bluer_agent.crawl.collect import collect, CollectionProperties
from bluer_agent.crawl.functions import url_to_filename
from bluer_agent.logger import logger

NAME = module.name(__file__, NAME)

properties = CollectionProperties()

parser = argparse.ArgumentParser(NAME)
parser.add_argument(
    "task",
    type=str,
    help="collect | review",
)
parser.add_argument(
    "--root",
    required=True,
    help="https://badkoobeh.com/",
)
parser.add_argument(
    "--page-count",
    type=int,
    default=25,
)
parser.add_argument(
    "--max-depth",
    type=int,
    default=2,
)
parser.add_argument(
    "--object_name",
    type=str,
    default="",
)
parser.add_argument(
    "--out",
    default="site_text.pkl.gz",
)
parser.add_argument(
    "--timeout",
    type=float,
    default=properties.timeout,
)
parser.add_argument(
    "--max-retries",
    type=int,
    default=properties.max_retries,
)
parser.add_argument(
    "--backoff-base",
    type=float,
    default=properties.backoff_base,
)
parser.add_argument(
    "--backoff-jitter",
    type=float,
    default=properties.backoff_jitter,
)
parser.add_argument(
    "--delay",
    type=float,
    default=properties.delay,
)
args = parser.parse_args()

success = False
if args.task == "collect":
    properties = CollectionProperties(
        timeout=args.timeout,
        max_retries=args.max_retries,
        backoff_base=args.backoff_base,
        backoff_jitter=args.backoff_jitter,
        delay=args.delay,
    )

    if args.root == "all":
        corpus_roots = get_from_object(args.object_name, "corpus", [])
        log_list(logger, "loaded", corpus_roots, "root(s)")

        success = True
        for root in tqdm(corpus_roots):
            if not collect(
                root=root,
                page_count=args.page_count,
                max_depth=args.max_depth,
                object_name=args.object_name,
                out="auto",
                properties=properties,
            ):
                success = False
                break
    else:
        success = collect(
            root=args.root,
            page_count=args.page_count,
            max_depth=args.max_depth,
            object_name=args.object_name,
            out=args.out,
            properties=properties,
        )
elif args.task == "review":
    list_of_filenames: List[str] = (
        list_of(
            objects.path_of(
                object_name=args.object_name,
                filename="*.pkl.gz",
            )
        )
        if args.root == "all"
        else [
            objects.path_of(
                object_name=args.object_name,
                filename="{}.pkl.gz".format(url_to_filename(args.root)),
            )
        ]
    )

    log_list(
        logger,
        "reviewing",
        [file_name(filename) for filename in list_of_filenames],
        "file(s)",
    )

    success = True
    for filename in tqdm(list_of_filenames):
        success, _ = file.load(filename)
        if not success:
            break
else:
    success = None
sys_exit(logger, NAME, args.task, success)
