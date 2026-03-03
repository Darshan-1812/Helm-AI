"use client";

import React, { useState, useEffect } from "react";
import { Sidebar, ApiKeyBar } from "../page";
import { getRuns } from "@/lib/api";

export default function RunsPage() {
    const [apiKey, setApiKey] = useState("");
    const [runs, setRuns] = useState<any[]>([]);
    const [total, setTotal] = useState(0);
    const [page, setPage] = useState(1);
    const [loading, setLoading] = useState(false);
    const [statusFilter, setStatusFilter] = useState("");
    const [agentFilter, setAgentFilter] = useState("");

    useEffect(() => {
        if (!apiKey) return;
        loadRuns();
    }, [apiKey, page, statusFilter, agentFilter]);

    async function loadRuns() {
        setLoading(true);
        try {
            const data = await getRuns({
                apiKey,
                page,
                pageSize: 20,
                status: statusFilter || undefined,
                agentName: agentFilter || undefined,
            });
            setRuns(data.runs || []);
            setTotal(data.total || 0);
        } catch (e) {
            console.error("Load runs error:", e);
        }
        setLoading(false);
    }

    return (
        <div className="app-layout">
            <Sidebar active="/runs" />
            <main className="main-content">
                <div className="page-header">
                    <h2>Agent Runs</h2>
                    <p>Browse and filter all agent execution sessions</p>
                </div>

                <ApiKeyBar apiKey={apiKey} setApiKey={setApiKey} />

                {apiKey && (
                    <>
                        {/* ── Filters ─────────────────────────── */}
                        <div
                            className="card"
                            style={{
                                display: "flex",
                                gap: "12px",
                                alignItems: "center",
                                marginBottom: "20px",
                                padding: "16px 20px",
                            }}
                        >
                            <label style={{ fontSize: "12px", color: "var(--text-muted)", fontWeight: 600 }}>
                                FILTERS
                            </label>
                            <select
                                value={statusFilter}
                                onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
                                style={{
                                    background: "rgba(0,0,0,0.3)",
                                    border: "1px solid var(--border-color)",
                                    borderRadius: "6px",
                                    padding: "6px 10px",
                                    color: "var(--text-primary)",
                                    fontSize: "13px",
                                }}
                            >
                                <option value="">All Statuses</option>
                                <option value="completed">Completed</option>
                                <option value="failed">Failed</option>
                                <option value="running">Running</option>
                                <option value="timeout">Timeout</option>
                            </select>
                            <input
                                type="text"
                                placeholder="Agent name..."
                                value={agentFilter}
                                onChange={(e) => { setAgentFilter(e.target.value); setPage(1); }}
                                style={{
                                    background: "rgba(0,0,0,0.3)",
                                    border: "1px solid var(--border-color)",
                                    borderRadius: "6px",
                                    padding: "6px 10px",
                                    color: "var(--text-primary)",
                                    fontSize: "13px",
                                    width: "200px",
                                }}
                            />
                            <span style={{ fontSize: "12px", color: "var(--text-muted)", marginLeft: "auto" }}>
                                {total} total runs
                            </span>
                        </div>

                        {/* ── Runs Table ──────────────────────── */}
                        <div className="card">
                            {loading ? (
                                <div className="loading"><div className="spinner" /> Loading runs...</div>
                            ) : runs.length === 0 ? (
                                <div className="empty-state">
                                    <h3>No runs found</h3>
                                    <p>Adjust filters or run the demo agent to generate data.</p>
                                </div>
                            ) : (
                                <>
                                    <table className="data-table">
                                        <thead>
                                            <tr>
                                                <th>Agent</th>
                                                <th>Status</th>
                                                <th>Input</th>
                                                <th>Cost</th>
                                                <th>Tokens</th>
                                                <th>Spans</th>
                                                <th>Latency</th>
                                                <th>Started</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {runs.map((run: any) => (
                                                <tr
                                                    key={run.id}
                                                    onClick={() =>
                                                        (window.location.href = `/runs/${run.id}?apiKey=${apiKey}`)
                                                    }
                                                >
                                                    <td>{run.agent_name}</td>
                                                    <td>
                                                        <span className={`badge ${run.status}`}>
                                                            {run.status}
                                                        </span>
                                                    </td>
                                                    <td style={{ maxWidth: "200px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                                                        {run.input_text || "—"}
                                                    </td>
                                                    <td>${(run.total_cost ?? 0).toFixed(4)}</td>
                                                    <td>{(run.total_tokens ?? 0).toLocaleString()}</td>
                                                    <td>{run.total_spans ?? 0}</td>
                                                    <td>
                                                        {run.latency_ms
                                                            ? `${(run.latency_ms / 1000).toFixed(1)}s`
                                                            : "—"}
                                                    </td>
                                                    <td>
                                                        {run.started_at
                                                            ? new Date(run.started_at).toLocaleString()
                                                            : "—"}
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>

                                    {/* ── Pagination ─────────────────── */}
                                    <div
                                        style={{
                                            display: "flex",
                                            justifyContent: "center",
                                            gap: "8px",
                                            marginTop: "16px",
                                        }}
                                    >
                                        <button
                                            className="btn btn-ghost"
                                            disabled={page <= 1}
                                            onClick={() => setPage((p) => p - 1)}
                                        >
                                            ← Previous
                                        </button>
                                        <span style={{ padding: "8px 16px", fontSize: "13px", color: "var(--text-muted)" }}>
                                            Page {page} of {Math.ceil(total / 20) || 1}
                                        </span>
                                        <button
                                            className="btn btn-ghost"
                                            disabled={page * 20 >= total}
                                            onClick={() => setPage((p) => p + 1)}
                                        >
                                            Next →
                                        </button>
                                    </div>
                                </>
                            )}
                        </div>
                    </>
                )}
            </main>
        </div>
    );
}
