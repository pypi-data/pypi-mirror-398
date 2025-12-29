from typing import Tuple, Dict, List
import gzip
import json
import numpy as np

from blueness import module
from bluer_objects import file, storage
from bluer_objects import objects
from bluer_objects.storage.policies import DownloadPolicy

from bluer_agent import NAME
from bluer_agent.rag.corpus.embed import embed_fn
from bluer_agent.logger import logger

NAME = module.name(__file__, NAME)


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


class Context:
    def __init__(
        self,
        object_name: str,
        download: bool = False,
    ):
        self.object_name = object_name

        if download:
            storage.download(
                self.object_name,
                policy=DownloadPolicy.DOESNT_EXIST,
            )

        # --- load corpus embeddings ---
        self.corpus_vec = np.load(
            objects.path_of(
                object_name=object_name,
                filename="corpus.embeddings.npy",
            )
        )

        self.corpus_meta_file = objects.path_of(
            object_name=self.object_name,
            filename="corpus.meta.jsonl.gz",
        )

        self.corpus_text_file = objects.path_of(
            object_name=self.object_name,
            filename="corpus.jsonl.gz",
        )

        logger.info(
            "{} created for {}.".format(
                self.__class__.__name__,
                self.object_name,
            )
        )

    def generate(
        self,
        query: str,
        top_k: int = 5,
    ) -> Tuple[bool, Dict]:
        logger.info(
            '{}[{}].generate("{}")'.format(
                self.__class__.__name__,
                self.object_name,
                query,
            )
        )

        # --- embed query ---
        q_vec = np.asarray(embed_fn([query])[0], dtype=np.float32)

        candidates: List[Tuple[float, dict]] = []

        with gzip.open(
            self.corpus_meta_file,
            "rt",
            encoding="utf-8",
        ) as meta_f, gzip.open(
            self.corpus_text_file,
            "rt",
            encoding="utf-8",
        ) as text_f:
            for i, (meta_line, text_line) in enumerate(zip(meta_f, text_f)):
                meta = json.loads(meta_line)

                record = json.loads(text_line)
                score = _cosine(q_vec, self.corpus_vec[i])

                candidates.append(
                    (
                        score,
                        {
                            "root": meta["root"],
                            "url": meta["url"],
                            "chunk_id": meta["chunk_id"],
                            "text": record["text"],
                        },
                    )
                )

        candidates.sort(key=lambda x: x[0], reverse=True)
        top = candidates[:top_k]

        chunks = [
            {
                **item,
                "score": round(score, 4),
            }
            for score, item in top
        ]

        for chunk in chunks:
            logger.info(
                "{} #{} @ {:.2f}: {}".format(
                    chunk["root"],
                    chunk["chunk_id"],
                    chunk["score"],
                    chunk["text"][:300],
                )
            )

        context = {
            "chunks": chunks,
        }

        file.save_text(
            objects.path_of(
                object_name=self.object_name,
                filename="result.txt",
            ),
            [
                f"query: {query}",
                "",
                "retrievals:",
            ]
            + [
                "{} #{} @ {:.2f}: {}".format(
                    chunk["root"],
                    chunk["chunk_id"],
                    chunk["score"],
                    chunk["text"][:300],
                )
                for chunk in chunks
            ],
            log=True,
        )

        return True, context

    def understand_reply(self, reply: str) -> Tuple[bool, str]:
        try:
            reply_dict = json.loads(reply)
        except Exception as e:
            logger.error(e)
            return False, ""

        for field in [
            "winner_root",
            "argument_fa",
        ]:
            if field not in reply_dict:
                logger.error(f"{field} not found.")
                return False, ""

        logger.info("🥇 winner is {}!".format(reply_dict["winner_root"]))

        return True, reply_dict["argument_fa"]
