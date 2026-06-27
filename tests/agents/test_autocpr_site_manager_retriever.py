"""Tests for the KB loader and the local BM25 retriever."""
from __future__ import annotations

from app.agents.autocpr_site_manager.kb_loader import KB_FILES, load_chunks
from app.agents.autocpr_site_manager.retriever import SiteManagerRetriever, tokenize
from app.agents.autocpr_site_manager.schemas import RetrievedChunk


def test_load_chunks_covers_all_kb_files():
    chunks = load_chunks()
    assert chunks, "KB should not be empty"
    sources = {c.source for c in chunks}
    # sop_source_analysis.md is optional-but-present; sop.md & kb_seed.md required.
    assert "sop.md" in sources
    assert "kb_seed.md" in sources
    # Every loaded source must be one of the declared KB files.
    assert sources <= set(KB_FILES)


def test_tokenize_is_bilingual():
    toks = tokenize("Bluetooth 黑屏")
    assert "bluetooth" in toks
    assert "黑" in toks and "屏" in toks  # CJK unigrams
    assert "黑屏" in toks  # CJK bigram


def test_search_returns_ranked_chunks():
    retriever = SiteManagerRetriever()
    results = retriever.search("选址评分表 scoring formula decision bands", top_k=3)
    assert 1 <= len(results) <= 3
    assert all(isinstance(r, RetrievedChunk) for r in results)
    assert all(r.score > 0 for r in results)
    # Sorted by descending score.
    assert results == sorted(results, key=lambda r: r.score, reverse=True)


def test_search_finds_smart_manikin_section():
    retriever = SiteManagerRetriever()
    results = retriever.search("Bluetooth 黑屏 manikin won't connect", top_k=3)
    assert results
    joined = " ".join(r.text.lower() for r in results)
    assert "bluetooth" in joined or "manikin" in joined


def test_empty_query_returns_nothing():
    retriever = SiteManagerRetriever()
    assert retriever.search("") == []
    assert retriever.search("   ") == []


def test_respects_top_k():
    retriever = SiteManagerRetriever()
    results = retriever.search("site opening ZIP demand competition", top_k=2)
    assert len(results) <= 2
