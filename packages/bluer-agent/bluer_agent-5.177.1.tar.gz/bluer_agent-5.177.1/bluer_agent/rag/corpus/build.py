from __future__ import annotations

import gzip
import json
import re

from tqdm import tqdm

from blueness import module
from bluer_options import string
from bluer_options.logger.config import log_list
from bluer_objects import objects
from bluer_objects.file import list_of
from bluer_objects.file import name as file_name
from bluer_objects.file import size as file_size

from bluer_agent import NAME
from bluer_agent.crawl import file
from bluer_agent.logger import logger


NAME = module.name(__file__, NAME)


def _root_name(filename: str) -> str:
    name = file_name(filename)
    for suffix in [".pkl.gz", ".pkl"]:
        if name.endswith(suffix):
            name = name[: -len(suffix)]
            break
    return name


def _normalize(text: str) -> str:
    text = text.replace("\u064a", "\u06cc")  # ي -> ی
    text = text.replace("\u0643", "\u06a9")  # ك -> ک
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _chunk(text: str, max_chars: int = 900, overlap: int = 120):
    text = _normalize(text)
    if not text:
        return
    step = max(1, max_chars - max(0, overlap))
    i = 0
    while i < len(text):
        chunk = text[i : i + max_chars].strip()
        if chunk:
            yield chunk
        i += step


def build(
    crawl_object_name: str,
    corpus_object_name: str,
) -> bool:
    logger.info(f"{NAME}.build: {crawl_object_name} -> {corpus_object_name}")

    list_of_filenames = list_of(
        objects.path_of(
            object_name=crawl_object_name,
            filename="*.pkl.gz",
        )
    )
    log_list(
        logger,
        "processing",
        [file_name(filename) for filename in list_of_filenames],
        "file(s)",
    )

    corpus_filename = objects.path_of(
        object_name=corpus_object_name,
        filename="corpus.jsonl.gz",
    )
    roots_filename = objects.path_of(
        object_name=corpus_object_name,
        filename="roots.json.gz",
    )

    roots = {}

    with gzip.open(corpus_filename, "wt", encoding="utf-8") as f:
        for filename in tqdm(list_of_filenames):
            root = _root_name(filename)
            logger.info("processing {} -> {} ...".format(file_name(filename), root))

            success, crawl = file.load(filename)
            if not success:
                return False

            agg_parts = []
            page_count = 0
            chunk_count = 0

            for url, text in tqdm(crawl.items()):
                page_count += 1
                text = _normalize(text)
                if text:
                    agg_parts.append(text[:2000])

                for chunk_id, chunk in enumerate(_chunk(text)):
                    record = {
                        "root": root,
                        "url": url,
                        "chunk_id": chunk_id,
                        "text": chunk,
                    }
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
                    chunk_count += 1

            roots[root] = {
                "root": root,
                "pages": page_count,
                "chunks": chunk_count,
                "text": _normalize(" ".join(agg_parts))[:200_000],
            }

    logger.info(
        "corpus -{}-> {}".format(
            string.pretty_bytes(file_size(corpus_filename)),
            corpus_filename,
        )
    )

    with gzip.open(roots_filename, "wt", encoding="utf-8") as f:
        f.write(json.dumps(roots, ensure_ascii=False))
    logger.info(
        "roots -{}-> {}".format(
            string.pretty_bytes(file_size(roots_filename)),
            roots_filename,
        ),
    )

    return True
