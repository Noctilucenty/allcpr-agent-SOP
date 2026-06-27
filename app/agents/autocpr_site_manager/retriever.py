"""Local keyword/BM25 retrieval over the agent's markdown KB.

Deterministic, dependency-light (stdlib only), and bilingual: English tokens are
matched as words while CJK runs are matched as character unigrams + bigrams so a
query like ``"黑屏"`` or ``"选址评分表"`` retrieves the right section. No paid
vector DB — the ``SiteManagerRetriever`` interface is intentionally narrow so it
can later be swapped for pgvector / Chroma / Pinecone without touching callers.
"""
from __future__ import annotations

import math
import re
from typing import Dict, List, Optional, Sequence

from .kb_loader import KBChunk, load_chunks
from .schemas import RetrievedChunk

_WORD_RE = re.compile(r"[a-z0-9]+")
_CJK_RUN_RE = re.compile(r"[一-鿿]+")


def tokenize(text: str) -> List[str]:
    """Tokenize ``text`` for retrieval.

    English/digits → lowercase word tokens. CJK → each character plus adjacent
    bigrams (so multi-character terms still match without a Chinese segmenter).
    """
    text = (text or "").lower()
    tokens: List[str] = _WORD_RE.findall(text)
    for run in _CJK_RUN_RE.findall(text):
        tokens.extend(run)  # unigrams: one token per character
        tokens.extend(run[i : i + 2] for i in range(len(run) - 1))  # bigrams
    return tokens


class SiteManagerRetriever:
    """BM25 retriever over the KB chunks.

    Parameters mirror standard BM25 (``k1``, ``b``). Build once and reuse — the
    index is computed in ``__init__``.
    """

    def __init__(
        self,
        chunks: Optional[Sequence[KBChunk]] = None,
        *,
        k1: float = 1.5,
        b: float = 0.75,
    ) -> None:
        self._chunks: List[KBChunk] = list(chunks) if chunks is not None else load_chunks()
        self._k1 = k1
        self._b = b

        self._doc_tokens: List[List[str]] = [tokenize(c.text) for c in self._chunks]
        self._doc_len: List[int] = [len(t) for t in self._doc_tokens]
        n = len(self._chunks)
        self._avgdl: float = (sum(self._doc_len) / n) if n else 0.0

        self._tf: List[Dict[str, int]] = []
        df: Dict[str, int] = {}
        for toks in self._doc_tokens:
            counts: Dict[str, int] = {}
            for tok in toks:
                counts[tok] = counts.get(tok, 0) + 1
            self._tf.append(counts)
            for tok in counts:
                df[tok] = df.get(tok, 0) + 1

        # BM25 idf with the +1 smoothing that keeps weights non-negative.
        self._idf: Dict[str, float] = {
            tok: math.log(1 + (n - d + 0.5) / (d + 0.5)) for tok, d in df.items()
        }

    def _score(self, query_tokens: Sequence[str], idx: int) -> float:
        tf = self._tf[idx]
        dl = self._doc_len[idx]
        avgdl = self._avgdl or 1.0
        score = 0.0
        for tok in query_tokens:
            freq = tf.get(tok)
            if not freq:
                continue
            idf = self._idf.get(tok, 0.0)
            denom = freq + self._k1 * (1 - self._b + self._b * dl / avgdl)
            score += idf * (freq * (self._k1 + 1)) / denom
        return score

    def search(self, query: str, top_k: int = 5) -> List[RetrievedChunk]:
        """Return up to ``top_k`` chunks ranked by BM25 relevance to ``query``.

        Only positively-scoring chunks are returned; an empty/whitespace query
        or an empty KB yields ``[]``.
        """
        q_tokens = tokenize(query)
        if not q_tokens or not self._chunks:
            return []
        scored = []
        for idx in range(len(self._chunks)):
            s = self._score(q_tokens, idx)
            if s > 0:
                scored.append((s, idx))
        # Highest score first; ties broken by document order for determinism.
        scored.sort(key=lambda pair: (-pair[0], pair[1]))
        results: List[RetrievedChunk] = []
        for s, idx in scored[:top_k]:
            chunk = self._chunks[idx]
            results.append(
                RetrievedChunk(source=chunk.source, text=chunk.text, score=round(float(s), 4))
            )
        return results
