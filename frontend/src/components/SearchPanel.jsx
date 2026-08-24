import { useState } from "react";
import { api } from "../api";
import { categoryStyle } from "../categoryStyle";

export default function SearchPanel({ onAdd }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const runSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const { results } = await api.search(query);
      setResults(results);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card p-6">
      <div className="mb-4 flex items-center gap-2">
        <span className="text-lg">🔎</span>
        <h2 className="font-display text-xl font-semibold text-ink">Semantic search</h2>
      </div>
      <form onSubmit={runSearch} className="mb-4 flex gap-2">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder='Try "organic fruits below 300"'
          className="flex-1 rounded-full border border-ink/10 bg-cream px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
        />
        <button
          type="submit"
          disabled={loading}
          className="rounded-full bg-teal-500 px-5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-teal-600 disabled:opacity-50"
        >
          {loading ? "Searching…" : "Search"}
        </button>
      </form>
      {error && <p className="text-sm text-berry-500">{error}</p>}
      <div className="grid gap-2 sm:grid-cols-2">
        {results.map((r) => {
          const style = categoryStyle(r.category);
          return (
            <div
              key={r.product}
              className="flex items-center justify-between rounded-xl px-3 py-2.5 text-sm"
              style={{ backgroundColor: `${style.color}14` }}
            >
              <div className="flex items-center gap-2.5">
                <span className="text-lg leading-none">{style.emoji}</span>
                <div>
                  <p className="font-medium text-ink">{r.product}</p>
                  <p className="text-xs text-ink/45">
                    {r.category} · ₹{r.price} · {Math.round(r.similarity * 100)}% match
                  </p>
                </div>
              </div>
              <button
                onClick={() => onAdd(r.product)}
                className="shrink-0 rounded-full bg-mango-500 px-3 py-1 text-xs font-semibold text-white shadow-sm hover:bg-mango-600"
              >
                + Add
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}