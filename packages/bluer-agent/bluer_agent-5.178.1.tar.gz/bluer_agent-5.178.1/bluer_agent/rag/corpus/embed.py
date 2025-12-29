from __future__ import annotations

import gzip
import json
from typing import Callable, List, Tuple
import requests
import numpy as np
from tqdm import tqdm

from blueness import module
from bluer_options import string
from bluer_options.logger.config import shorten_text
from bluer_objects import objects, file

from bluer_agent import NAME
from bluer_agent import env
from bluer_agent.logger import logger


NAME = module.name(__file__, NAME)


def _read_jsonl_gz(filename: str):
    with gzip.open(filename, "rt", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def _read_json_gz(filename: str):
    with gzip.open(filename, "rt", encoding="utf-8") as f:
        return json.loads(f.read())


import requests


def embed_fn(texts):
    logger.info("embed_fn({})".format(shorten_text(" ".join(texts))))

    r = requests.post(
        f"{env.BLUER_AGENT_EMBEDDING_ENDPOINT}/embeddings",
        headers={
            "Authorization": f"apikey {env.BLUER_AGENT_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": env.BLUER_AGENT_EMBEDDING_MODEL_NAME,
            "input": texts,
        },
        timeout=60,
    )
    r.raise_for_status()
    data = r.json()
    return [item["embedding"] for item in data["data"]]


def embed(
    object_name: str,
    embed_fn: Callable[[List[str]], List[List[float]]],
    batch_size: int = 64,
) -> bool:
    logger.info(f"{NAME}.embed: {object_name}")

    corpus_filename = objects.path_of(
        object_name=object_name,
        filename="corpus.jsonl.gz",
    )
    roots_filename = objects.path_of(
        object_name=object_name,
        filename="roots.json.gz",
    )

    chunks_vec_filename = objects.path_of(
        object_name=object_name,
        filename="corpus.embeddings.npy",
    )
    chunks_meta_filename = objects.path_of(
        object_name=object_name,
        filename="corpus.meta.jsonl.gz",
    )

    roots_vec_filename = objects.path_of(
        object_name=object_name,
        filename="roots.embeddings.npy",
    )
    roots_meta_filename = objects.path_of(
        object_name=object_name,
        filename="roots.meta.json.gz",
    )

    # --- embed roots (for "most relevant root" selection) ---
    roots = _read_json_gz(roots_filename)
    root_names = sorted(list(roots.keys()))
    root_texts = [roots[name].get("text", "") for name in root_names]

    root_vectors = []
    for i in tqdm(range(0, len(root_texts), batch_size), desc="embedding roots"):
        batch = root_texts[i : i + batch_size]
        root_vectors.extend(embed_fn(batch))

    root_vectors = np.asarray(root_vectors, dtype=np.float32)
    np.save(roots_vec_filename, root_vectors)

    roots_meta = {
        "roots": root_names,
        "shape": list(root_vectors.shape),
        "source": roots_filename,
    }
    with gzip.open(roots_meta_filename, "wt", encoding="utf-8") as f:
        f.write(json.dumps(roots_meta, ensure_ascii=False))

    logger.info(
        "roots vec -{}-> {}".format(
            string.pretty_bytes(file.size(roots_vec_filename)),
            roots_vec_filename,
        )
    )
    logger.info(
        "roots meta -{}-> {}".format(
            string.pretty_bytes(file.size(roots_meta_filename)),
            roots_meta_filename,
        )
    )

    # --- embed chunks (for evidence extraction within selected root) ---
    vectors = []
    batch_texts: List[str] = []
    batch_meta: List[dict] = []

    with gzip.open(chunks_meta_filename, "wt", encoding="utf-8") as meta_f:
        for record in tqdm(_read_jsonl_gz(corpus_filename), desc="embedding corpus"):
            text = record.get("text", "")
            if not text:
                continue

            batch_texts.append(text)
            batch_meta.append(
                {
                    "root": record.get("root", ""),
                    "url": record.get("url", ""),
                    "chunk_id": record.get("chunk_id", -1),
                }
            )

            if len(batch_texts) >= batch_size:
                batch_vecs = embed_fn(batch_texts)
                vectors.extend(batch_vecs)

                for m in batch_meta:
                    meta_f.write(json.dumps(m, ensure_ascii=False) + "\n")

                batch_texts = []
                batch_meta = []

        if batch_texts:
            batch_vecs = embed_fn(batch_texts)
            vectors.extend(batch_vecs)

            for m in batch_meta:
                meta_f.write(json.dumps(m, ensure_ascii=False) + "\n")
    logger.info(
        "chunk meta -{}-> {}".format(
            string.pretty_bytes(file.size(chunks_meta_filename)),
            chunks_meta_filename,
        )
    )

    vectors = np.asarray(vectors, dtype=np.float32)
    np.save(chunks_vec_filename, vectors)
    logger.info(
        "chunks vec -{}-{}-> {}".format(
            string.pretty_shape_of_matrix(vectors),
            string.pretty_bytes(file.size(chunks_vec_filename)),
            chunks_vec_filename,
        )
    )

    return True
