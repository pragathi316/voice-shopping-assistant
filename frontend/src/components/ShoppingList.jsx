import { categoryStyle } from "../categoryStyle";

export default function ShoppingList({ items, loading, itemCount, onRemove, onUpdateQty }) {
  return (
    <div className="card p-6">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="font-display text-xl font-semibold text-ink">Your list</h2>
        {itemCount > 0 && (
          <span className="rounded-full bg-teal-500/10 px-2.5 py-1 text-xs font-semibold text-teal-600">
            {itemCount} item{itemCount === 1 ? "" : "s"}
          </span>
        )}
      </div>
      {loading && <p className="text-sm text-ink/50">Loading…</p>}
      {!loading && items.length === 0 && (
        <div className="rounded-xl border border-dashed border-ink/15 py-8 text-center">
          <p className="text-2xl">🛒</p>
          <p className="mt-2 text-sm text-ink/50">Nothing here yet — say "add milk" to start.</p>
        </div>
      )}
      <ul className="space-y-2">
        {items.map((item) => {
          const style = categoryStyle(item.category);
          return (
            <li
              key={item.product}
              className="flex items-center justify-between rounded-xl px-3 py-2.5"
              style={{ backgroundColor: `${style.color}14` }}
            >
              <div className="flex items-center gap-3">
                <span className="text-xl leading-none">{style.emoji}</span>
                <div>
                  <p className="font-medium text-ink">{item.product}</p>
                  {item.category && <p className="text-xs text-ink/45">{item.category}</p>}
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-1 rounded-full bg-white px-1.5 py-1 shadow-sm">
                  <button
                    className="flex h-6 w-6 items-center justify-center rounded-full text-sm text-ink/60 hover:bg-ink/5"
                    onClick={() => onUpdateQty(item.product, Math.max(1, item.quantity - 1))}
                    aria-label={`Decrease quantity of ${item.product}`}
                  >
                    −
                  </button>
                  <span className="w-5 text-center text-sm font-medium">{item.quantity}</span>
                  <button
                    className="flex h-6 w-6 items-center justify-center rounded-full text-sm text-ink/60 hover:bg-ink/5"
                    onClick={() => onUpdateQty(item.product, item.quantity + 1)}
                    aria-label={`Increase quantity of ${item.product}`}
                  >
                    +
                  </button>
                </div>
                <button
                  onClick={() => onRemove(item.product)}
                  className="text-xs font-semibold uppercase tracking-wide text-berry-500 hover:text-berry-600"
                >
                  Remove
                </button>
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}