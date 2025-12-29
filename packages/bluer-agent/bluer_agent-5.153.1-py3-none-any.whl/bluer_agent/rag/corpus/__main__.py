import argparse

from blueness import module
from blueness.argparse.generic import sys_exit

from bluer_agent import NAME
from bluer_agent.rag.corpus.build import build
from bluer_agent.rag.corpus.embed import embed, embed_fn
from bluer_agent.logger import logger

NAME = module.name(__file__, NAME)

parser = argparse.ArgumentParser(NAME)
parser.add_argument(
    "task",
    type=str,
    help="build_and_embed",
)
parser.add_argument(
    "--crawl_object_name",
    type=str,
)
parser.add_argument(
    "--corpus_object_name",
    type=str,
)
args = parser.parse_args()

success = False
if args.task == "build_and_embed":
    success = build(
        crawl_object_name=args.crawl_object_name,
        corpus_object_name=args.corpus_object_name,
    )

    if success:
        success = embed(
            object_name=args.corpus_object_name,
            embed_fn=embed_fn,
        )
else:
    success = None

sys_exit(logger, NAME, args.task, success)
