"use client";

import React, { useState, useEffect } from "react";
import { useParams, useSearchParams } from "next/navigation";
import { Sidebar } from "../../page";
import { getRun } from "@/lib/api";

export default function RunDetailPage() {
    const params = useParams();
    const searchParams = useSearchParams();
    const runId = params.id as string;
    const initialApiKey = searchParams.get("apiKey") || "";

    const [apiKey, setApiKey] = useState(initialApiKey);
    const [run, setRun] = useState<any>(null);
    const [selectedSpan, setSelectedSpan] = useState<any>(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (!apiKey || !runId) return;
        loadRun();
    }, [apiKey, runId]);

    async function loadRun() {
        setLoading(true);
        try {
            const data = await getRun(runId, apiKey);
            setRun(data);
            if (data.spans?.length > 0) {
                setSelectedSpan(data.spans[0]);
            }
        } catch (e) {
            console.error("Load run error:", e);
        }
        setLoading(false);
    }

    const spanKindColors: Record<string, string> = {
        agent: "var(--accent-purple)",
        llm: "var(--accent-blue)",
        tool: "var(--accent-green)",
        retriever: "var(--accent-cyan)",
        chain: "var(--accent-amber)",
        embedding: "var(--accent-pink)",
        reranker: "var(--accent-amber)",
    };

    return (
        <div className="app-layout">
            <Sidebar active="/runs" />
            <main className="main-content">
                {!apiKey && (
                    <div className="api-key-bar">
                        <label>🔑 API Key</label>
                        <input
                            type="text"
                            placeholder="Paste your API key..."
                            value={apiKey}
                            onChange={(e) => setApiKey(e.target.value)}
                        />
                    </div>
                )}

                {loading && (
                    <div className="loading">
                        <div className="spinner" /> Loading trace...
                    </div>
                )}

                {run && (
                    <>
                        {/* ── Run Header ───────────────────────── */}
                        <div className="page-header">
                            <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                                <h2>{run.agent_name}</h2>
                                <span className={`badge ${run.status}`}>{run.status}</span>
                            </div>
                            <p>
                                Run ID: <code style={{ fontSize: "12px" }}>{run.id}</code>
                            </p>
                        </div>

                        {/* ── Run Stats ────────────────────────── */}
                        <div className="card-grid card-grid-4" style={{ marginBottom: "24px" }}>
                            <div className="card stat-card green" style={{ padding: "16px 20px" }}>
                                <div className="stat-label">Cost</div>
                                <div className="stat-value" style={{ fontSize: "24px" }}>
                                    ${(run.total_cost ?? 0).toFixed(4)}
                                </div>
                            </div>
                            <div className="card stat-card blue" style={{ padding: "16px 20px" }}>
                                <div className="stat-label">Tokens</div>
                                <div className="stat-value" style={{ fontSize: "24px" }}>
                                    {(run.total_tokens ?? 0).toLocaleString()}
                                </div>
                            </div>
                            <div className="card stat-card purple" style={{ padding: "16px 20px" }}>
                                <div className="stat-label">Spans</div>
                                <div className="stat-value" style={{ fontSize: "24px" }}>
                                    {run.total_spans ?? 0}
                                </div>
                            </div>
                            <div className="card stat-card amber" style={{ padding: "16px 20px" }}>
                                <div className="stat-label">Latency</div>
                                <div className="stat-value" style={{ fontSize: "24px" }}>
                                    {run.latency_ms ? `${(run.latency_ms / 1000).toFixed(1)}s` : "—"}
                                </div>
                            </div>
                        </div>

                        {/* ── Input/Output ─────────────────────── */}
                        <div className="card-grid card-grid-2" style={{ marginBottom: "24px" }}>
                            <div className="card">
                                <h4 style={{ fontSize: "13px", color: "var(--text-muted)", marginBottom: "8px" }}>
                                    INPUT
                                </h4>
                                <div className="trace-span span-io" style={{ margin: 0 }}>
                                    {run.input_text || "—"}
                                </div>
                            </div>
                            <div className="card">
                                <h4 style={{ fontSize: "13px", color: "var(--text-muted)", marginBottom: "8px" }}>
                                    OUTPUT
                                </h4>
                                <div className="trace-span span-io" style={{ margin: 0 }}>
                                    {run.output_text || "—"}
                                </div>
                            </div>
                        </div>

                        {/* ── Trace Timeline ───────────────────── */}
                        <h3 style={{ fontSize: "16px", fontWeight: 600, marginBottom: "12px" }}>
                            📼 Session Recording — Trace Timeline
                        </h3>

                        <div style={{ display: "flex", gap: "20px" }}>
                            {/* ── Span List ─────────────────────── */}
                            <div style={{ flex: "1", minWidth: 0 }}>
                                <div className="trace-timeline">
                                    {(run.spans || []).map((span: any, idx: number) => (
                                        <div
                                            key={span.id}
                                            className={`trace-span ${selectedSpan?.id === span.id ? "selected" : ""} ${span.error ? "has-error" : ""}`}
                                            onClick={() => setSelectedSpan(span)}
                                        >
                                            <div className="span-bar">
                                                <div className="span-header">
                                                    <span className={`span-kind ${span.span_kind}`}>
                                                        {span.span_kind}
                                                    </span>
                                                    <span className="span-name">{span.name}</span>
                                                </div>
                                                <div className="span-meta">
                                                    {span.model && <span>🤖 {span.model}</span>}
                                                    {span.latency_ms && (
                                                        <span>⏱ {(span.latency_ms / 1000).toFixed(2)}s</span>
                                                    )}
                                                    {span.tokens_total && (
                                                        <span>📊 {span.tokens_total} tokens</span>
                                                    )}
                                                    {span.cost && <span>💰 ${span.cost.toFixed(4)}</span>}
                                                    {span.error && <span style={{ color: "var(--accent-red)" }}>❌ Error</span>}
                                                </div>
                                            </div>
                                            {/* ── Latency Bar ───────────── */}
                                            <div
                                                style={{
                                                    width: "100px",
                                                    display: "flex",
                                                    alignItems: "center",
                                                }}
                                            >
                                                <div
                                                    style={{
                                                        height: "4px",
                                                        borderRadius: "2px",
                                                        background:
                                                            spanKindColors[span.span_kind] || "var(--text-muted)",
                                                        width: `${Math.min(100, ((span.latency_ms || 0) / Math.max(...(run.spans || []).map((s: any) => s.latency_ms || 0), 1)) * 100)}%`,
                                                        minWidth: "10px",
                                                    }}
                                                />
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {/* ── Span Detail Panel ──────────────── */}
                            {selectedSpan && (
                                <div className="card" style={{ width: "400px", flexShrink: 0 }}>
                                    <h4
                                        style={{
                                            fontSize: "14px",
                                            fontWeight: 600,
                                            marginBottom: "16px",
                                            display: "flex",
                                            alignItems: "center",
                                            gap: "8px",
                                        }}
                                    >
                                        <span className={`span-kind ${selectedSpan.span_kind}`}>
                                            {selectedSpan.span_kind}
                                        </span>
                                        {selectedSpan.name}
                                    </h4>

                                    <div style={{ fontSize: "12px", display: "flex", flexDirection: "column", gap: "12px" }}>
                                        {selectedSpan.model && (
                                            <div>
                                                <span style={{ color: "var(--text-muted)" }}>Model: </span>
                                                <span>{selectedSpan.model}</span>
                                            </div>
                                        )}

                                        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px" }}>
                                            {selectedSpan.tokens_prompt != null && (
                                                <div>
                                                    <span style={{ color: "var(--text-muted)" }}>Prompt tokens: </span>
                                                    {selectedSpan.tokens_prompt}
                                                </div>
                                            )}
                                            {selectedSpan.tokens_completion != null && (
                                                <div>
                                                    <span style={{ color: "var(--text-muted)" }}>Completion tokens: </span>
                                                    {selectedSpan.tokens_completion}
                                                </div>
                                            )}
                                            {selectedSpan.cost != null && (
                                                <div>
                                                    <span style={{ color: "var(--text-muted)" }}>Cost: </span>
                                                    <span style={{ color: "var(--accent-green)" }}>
                                                        ${selectedSpan.cost.toFixed(6)}
                                                    </span>
                                                </div>
                                            )}
                                            {selectedSpan.latency_ms != null && (
                                                <div>
                                                    <span style={{ color: "var(--text-muted)" }}>Latency: </span>
                                                    {(selectedSpan.latency_ms / 1000).toFixed(2)}s
                                                </div>
                                            )}
                                        </div>

                                        {selectedSpan.error && (
                                            <div
                                                style={{
                                                    background: "rgba(239, 68, 68, 0.1)",
                                                    border: "1px solid rgba(239, 68, 68, 0.2)",
                                                    borderRadius: "6px",
                                                    padding: "10px",
                                                }}
                                            >
                                                <div style={{ color: "var(--accent-red)", fontWeight: 600, marginBottom: "4px" }}>
                                                    {selectedSpan.error_type || "Error"}
                                                </div>
                                                {selectedSpan.error}
                                            </div>
                                        )}

                                        {selectedSpan.input_data && (
                                            <div>
                                                <div style={{ color: "var(--text-muted)", marginBottom: "4px", fontWeight: 600 }}>
                                                    INPUT
                                                </div>
                                                <div className="span-io">{selectedSpan.input_data}</div>
                                            </div>
                                        )}

                                        {selectedSpan.output_data && (
                                            <div>
                                                <div style={{ color: "var(--text-muted)", marginBottom: "4px", fontWeight: 600 }}>
                                                    OUTPUT
                                                </div>
                                                <div className="span-io">{selectedSpan.output_data}</div>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            )}
                        </div>
                    </>
                )}
            </main>
        </div>
    );
}
