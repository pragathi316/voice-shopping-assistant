"""
Unit tests for the collaborative-filtering (co-occurrence) part of the
recommender. These don't require downloading any HF/sentence-transformer
models, so they run anywhere without network access - a lightweight
StubStore stands in for VectorStore so we can still exercise the blended
scoring path deterministically.

Run with:  pytest backend/tests/test_recommender.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend.app.recommender import Recommender


class _StubProduct:
    def __init__(self, name, category="Test", price=10.0):
        self.name = name
        self.category = category
        self.price = price


class StubStore:
    """Minimal stand-in for VectorStore: no embeddings, no network calls.
    `substitutes` returns nothing so tests can isolate the collaborative
    signal, or be monkeypatched per-test to exercise the content signal."""

    def __init__(self, substitute_map=None):
        self._substitute_map = substitute_map or {}

    def find_product(self, name):
        return _StubProduct(name)

    def substitutes(self, product_name, top_k=20):
        return self._substitute_map.get(product_name, [])


def _write_history(tmp_path, rows):
    path = tmp_path / "history.csv"
    with open(path, "w") as f:
        f.write("user_id,product,timestamp\n")
        for r in rows:
            f.write(f"{r[0]},{r[1]},2025-01-01T00:00:00\n")
    return str(path)


def test_co_occurrence_symmetric(tmp_path):
    rows = [
        ("u1", "Milk"), ("u1", "Bread"),
        ("u2", "Milk"), ("u2", "Bread"),
    ]
    history_path = _write_history(tmp_path, rows)
    rec = Recommender(StubStore(), history_path=history_path)
    assert rec.co_occurrence["Milk"]["Bread"] == 2
    assert rec.co_occurrence["Bread"]["Milk"] == 2


def test_recommend_excludes_seed_items(tmp_path):
    rows = [
        ("u1", "Milk"), ("u1", "Bread"), ("u1", "Butter"),
        ("u2", "Milk"), ("u2", "Bread"),
    ]
    history_path = _write_history(tmp_path, rows)
    rec = Recommender(StubStore(), history_path=history_path)
    results = rec.recommend(["Milk"], top_k=5)
    names = [r["product"] for r in results]
    assert "Milk" not in names
    assert "Bread" in names  # co-occurs with Milk twice


def test_recommend_cold_start_falls_back_to_popularity(tmp_path):
    rows = [
        ("u1", "Milk"), ("u2", "Milk"), ("u3", "Milk"),
        ("u4", "Bread"),
    ]
    history_path = _write_history(tmp_path, rows)
    rec = Recommender(StubStore(), history_path=history_path)
    results = rec.recommend([], top_k=2)
    assert results[0]["product"] == "Milk"  # most popular item overall


def test_recommend_blends_collab_and_content_reason(tmp_path):
    rows = [("u1", "Milk"), ("u1", "Almond Milk"), ("u2", "Milk"), ("u2", "Almond Milk")]
    history_path = _write_history(tmp_path, rows)
    store = StubStore(substitute_map={
        "Milk": [{"product": "Almond Milk", "similarity": 0.9}],
    })
    rec = Recommender(store, history_path=history_path)
    results = rec.recommend(["Milk"], top_k=5)
    almond = next(r for r in results if r["product"] == "Almond Milk")
    assert "purchase patterns" in almond["reason"] and "semantically similar" in almond["reason"]
