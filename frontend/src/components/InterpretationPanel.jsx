export default function InterpretationPanel({ result, loading, error }) {
  if (loading) {
    return (
      <div className="card flex items-center gap-3 p-5 text-sm text-ink/60">
        <span className="waveform" aria-hidden="true">
          <span /><span /><span /><span /><span />
        </span>
        Working out what you meant…
      </div>
    );
  }

  if (error) {
    return (
      <div className="card p-5 text-sm" style={{ backgroundColor: "#e85d7514", color: "#cf3f59" }}>
        ⚠️ {error}
      </div>
    );
  }

  if (!result) {
    return (
      <div className="card border border-dashed border-ink/15 p-5 text-sm text-ink/50 shadow-none">
        Tap the mic and say something like <em>"Add two bottles of milk"</em> or{" "}
        <em>"I want healthy snacks under 200."</em>
      </div>
    );
  }

  const { transcript, intent, intent_confidence, entities, message } = result;

  return (
    <div className="card p-5 space-y-3">
      <p className="text-xs font-semibold uppercase tracking-wide text-ink/40">You said</p>
      <p className="font-display text-lg italic text-ink">"{transcript}"</p>

      <div className="flex flex-wrap gap-2 pt-1">
        <span className="rounded-full bg-teal-500 px-3 py-1 text-xs font-semibold text-white">
          {intent} · {Math.round(intent_confidence * 100)}%
        </span>
        {entities.product && <EntityTag label="product" value={entities.product} />}
        {entities.quantity != null && <EntityTag label="qty" value={entities.quantity} />}
        {entities.category && <EntityTag label="category" value={entities.category} />}
        {entities.brand && <EntityTag label="brand" value={entities.brand} />}
        {entities.price_max != null && <EntityTag label="under" value={entities.price_max} />}
        {entities.price_min != null && <EntityTag label="over" value={entities.price_min} />}
      </div>

      <p className="pt-1 text-sm text-ink/80">{message}</p>
    </div>
  );
}

function EntityTag({ label, value }) {
  return (
    <span className="rounded-full bg-mango-500/15 px-3 py-1 text-xs text-ink/70">
      <span className="opacity-50">{label}:</span> {String(value)}
    </span>
  );
}