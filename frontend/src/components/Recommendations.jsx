import { categoryStyle } from "../categoryStyle";

export default function Recommendations({ items, loading, onAdd }) {
  return (
    <div className="card p-6">
      <div className="mb-1 flex items-center gap-2">
        <span className="text-lg">✨</span>
        <h2 className="font-display text-xl font-semibold text-ink">You might also need</h2>
      </div>
      <p className="mb-4 text-xs text-ink/45">Purchase-pattern overlap + semantic similarity</p>
      {loading && <p className="text-sm text-ink/50">Thinking it over…</p>}
      {!loading && items.length === 0 && (
        <div className="rounded-xl border border-dashed border-ink/15 py-8 text-center">
          <p className="text-2xl">💡</p>
          <p className="mt-2 text-sm text-ink/50">Add a few items and suggestions will show up here.</p>
        </div>
      )}
      <div className="space-y-2">
        {items.map((rec) => {
          const style = categoryStyle(rec.category);
          return (
            <div
              key={rec.product}
              className="flex items-start justify-between gap-3 rounded-xl px-3 py-2.5"
              style={{ backgroundColor: `${style.color}14` }}
            >
              <div className="flex items-start gap-3">
                <span className="text-xl leading-none">{style.emoji}</span>
                <div>
                  <div className="flex items-center gap-2">
                    <p className="font-medium text-ink">{rec.product}</p>
                    {rec.price != null && <span className="text-xs text-ink/40">₹{rec.price}</span>}
                  </div>
                  <p className="mt-0.5 text-xs text-ink/55">{rec.reason}</p>
                </div>
              </div>
              <button
                onClick={() => onAdd(rec.product)}
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