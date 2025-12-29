import argparse
import base64

from blueness import module
from blueness.argparse.generic import sys_exit

from bluer_agent import NAME
from bluer_agent.rag.query import query
from bluer_agent.logger import logger

NAME = module.name(__file__, NAME)

parser = argparse.ArgumentParser(NAME)
parser.add_argument(
    "task",
    type=str,
    help="query",
)
parser.add_argument(
    "--object_name",
    type=str,
)
parser.add_argument(
    "--encoded_query",
    type=str,
)
parser.add_argument(
    "--top_k",
    type=int,
    default=5,
)
args = parser.parse_args()

success = False
if args.task == "query":
    success, _ = query(
        object_name=args.object_name,
        query=base64.b64decode(args.encoded_query).decode("utf-8"),
        top_k=args.top_k,
    )
else:
    success = None

sys_exit(logger, NAME, args.task, success)
