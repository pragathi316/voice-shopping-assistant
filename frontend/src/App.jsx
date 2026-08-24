import { useCallback, useEffect, useState } from "react";
import VoiceButton from "./components/VoiceButton.jsx";
import InterpretationPanel from "./components/InterpretationPanel.jsx";
import ShoppingList from "./components/ShoppingList.jsx";
import Recommendations from "./components/Recommendations.jsx";
import SearchPanel from "./components/SearchPanel.jsx";
import { api } from "./api";

const USER_ID = "guest";

export default function App() {
  const [nluResult, setNluResult] = useState(null);
  const [nluLoading, setNluLoading] = useState(false);
  const [nluError, setNluError] = useState(null);

  const [list, setList] = useState([]);
  const [listLoading, setListLoading] = useState(true);

  const [recs, setRecs] = useState([]);
  const [recsLoading, setRecsLoading] = useState(true);

  const [typedCommand, setTypedCommand] = useState("");

  const refreshList = useCallback(async () => {
    setListLoading(true);
    try {
      const data = await api.getList(USER_ID);
      setList(data);
    } catch (e) {
      setNluError(e.message);
    } finally {
      setListLoading(false);
    }
  }, []);

  const refreshRecs = useCallback(async () => {
    setRecsLoading(true);
    try {
      const data = await api.getRecommendations(USER_ID);
      setRecs(data);
    } catch (e) {
      // recommendations are best-effort; don't block the rest of the UI
    } finally {
      setRecsLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshList();
    refreshRecs();
  }, [refreshList, refreshRecs]);

  const handleVoiceResult = async (transcript) => {
    setNluLoading(true);
    setNluError(null);
    try {
      const result = await api.processVoice(transcript, USER_ID);
      setNluResult(result);
      await refreshList();
      await refreshRecs();
    } catch (e) {
      setNluError(e.message);
    } finally {
      setNluLoading(false);
    }
  };

  const handleTypedSubmit = (e) => {
    e.preventDefault();
    if (!typedCommand.trim()) return;
    handleVoiceResult(typedCommand);
    setTypedCommand("");
  };

  const handleRemove = async (product) => {
    try {
      await api.removeItem(USER_ID, product);
      await refreshList();
      await refreshRecs();
    } catch (e) {
      setNluError(e.message);
    }
  };

  const handleUpdateQty = async (product, quantity) => {
    try {
      await api.updateItem(USER_ID, product, quantity);
      await refreshList();
    } catch (e) {
      setNluError(e.message);
    }
  };

  const handleAdd = async (product) => {
    try {
      await api.addItem(USER_ID, product, 1);
      await refreshList();
      await refreshRecs();
    } catch (e) {
      setNluError(e.message);
    }
  };

  const itemCount = list.reduce((sum, i) => sum + i.quantity, 0);

  return (
    <div className="min-h-screen bg-cream">
      <header className="px-6 py-5">
        <div className="mx-auto max-w-4xl flex items-center gap-2">
          <span className="text-2xl">🌱</span>
          <div>
            <h1 className="font-display text-xl font-semibold text-ink">Sprout</h1>
          </div>
        </div>
      </header>

      <section className="relative overflow-hidden">
        <div className="hero-blob" />
        <div className="relative z-10 mx-auto max-w-4xl px-6 pb-10 pt-4 text-center">
          <span className="inline-block rounded-full bg-teal-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-teal-600">
            Voice · NLU · Vector Search · Recommender
          </span>
          <h2 className="font-display mt-4 text-4xl font-semibold leading-tight text-ink sm:text-5xl">
            Say it.<br className="sm:hidden" /> It's on the list.
          </h2>
          <p className="mx-auto mt-3 max-w-md text-sm text-ink/60">
            Talk to your shopping list the way you'd talk to a person — Sprout figures out
            what you meant, not just what you typed.
          </p>

          <div className="mt-8 flex flex-col items-center gap-4">
            <div className="flex items-center gap-4">
              {!nluLoading && (
                <div className="waveform" aria-hidden="true">
                  <span /><span /><span /><span /><span />
                </div>
              )}
              <VoiceButton onResult={handleVoiceResult} onError={setNluError} disabled={nluLoading} />
              {!nluLoading && (
                <div className="waveform" aria-hidden="true" style={{ transform: "scaleX(-1)" }}>
                  <span /><span /><span /><span /><span />
                </div>
              )}
            </div>

            <form onSubmit={handleTypedSubmit} className="flex w-full max-w-md gap-2">
              <input
                value={typedCommand}
                onChange={(e) => setTypedCommand(e.target.value)}
                placeholder='No mic? Type: "add two bottles of milk"'
                className="flex-1 rounded-full border border-ink/10 bg-white px-4 py-2.5 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
              />
              <button
                type="submit"
                className="rounded-full bg-teal-500 px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-teal-600"
              >
                Send
              </button>
            </form>
          </div>
        </div>
      </section>

      <main className="mx-auto max-w-4xl px-6 pb-16 space-y-8">
        <InterpretationPanel result={nluResult} loading={nluLoading} error={nluError} />

        <div className="grid gap-6 md:grid-cols-2">
          <ShoppingList
            items={list}
            loading={listLoading}
            itemCount={itemCount}
            onRemove={handleRemove}
            onUpdateQty={handleUpdateQty}
          />
          <Recommendations items={recs} loading={recsLoading} onAdd={handleAdd} />
        </div>

        <SearchPanel onAdd={handleAdd} />
      </main>

      <footer className="mx-auto max-w-4xl px-6 pb-10 text-xs text-ink/40">
        Voice Command Shopping Assistant — intent classification, entity extraction, semantic search &
        a hybrid recommender, all model-driven.
      </footer>
    </div>
  );
}