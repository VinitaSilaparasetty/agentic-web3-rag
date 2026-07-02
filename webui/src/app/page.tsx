"use client";
import { useState } from "react";
import { API_BASE } from "@/lib/config";

type Result = {
  score?: number;
  url?: string;
  project?: string | null;
  source_id?: string | null;
  snippet?: string | null;
};

export default function Page() {
  const [q, setQ] = useState("geth rpc");
  const [collection, setCollection] = useState("web3_docs_staging");
  const [loading, setLoading] = useState(false);
  const [items, setItems] = useState<Result[]>([]);
  const [err, setErr] = useState<string | null>(null);

  async function search() {
    setLoading(true);
    setErr(null);
    setItems([]);
    try {
      const params = new URLSearchParams({
        q,
        k: "5",
        project: "ethereum,geth",
        collection
      });
      const r = await fetch(`${API_BASE}/search?` + params.toString(), {
        headers: { "Accept": "application/json" }
      });
      if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
      const data = await r.json();
      setItems(data.results || []);
    } catch (e: any) {
      setErr(e?.message || "Request failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="p-6 max-w-2xl mx-auto">
      <h1 className="text-2xl font-semibold mb-4">Web3 Docs Search</h1>

      <div className="flex flex-col gap-2 mb-4">
        <input
          className="border px-3 py-2 rounded"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Ask anything… e.g. 'eth_getBalance in geth'"
        />
        <input
          className="border px-3 py-2 rounded"
          value={collection}
          onChange={(e) => setCollection(e.target.value)}
          placeholder="Qdrant collection (e.g. web3_docs_staging)"
        />
        <button
          className="bg-black text-white px-4 py-2 rounded disabled:opacity-50"
          onClick={search}
          disabled={loading}
        >
          {loading ? "Searching…" : "Search"}
        </button>
      </div>

      {err && <div className="text-red-600 mb-3">Error: {err}</div>}

      <ul className="space-y-4">
        {items.map((it, i) => (
          <li key={i} className="border p-4 rounded">
            <a className="font-medium underline" href={it.url} target="_blank" rel="noreferrer">
              {it.url}
            </a>
            {it.project && <div className="text-xs mt-1 opacity-70">project: {it.project}</div>}
            {typeof it.score === "number" && (
              <div className="text-xs opacity-70">score: {it.score.toFixed(3)}</div>
            )}
            {it.snippet && <div className="text-sm mt-2">{it.snippet}</div>}
          </li>
        ))}
      </ul>
    </main>
  );
}
