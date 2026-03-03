"use client";

import React, { useState, useEffect } from "react";
import { Sidebar, ApiKeyBar } from "../page";
import { getCostSummary } from "@/lib/api";

export default function CostsPage() {
    const [apiKey, setApiKey] = useState("");
    const [data, setData] = useState<any>(null);
    const [loading, setLoading] = useState(false);
    const [days, setDays] = useState(30);

    useEffect(() => {
        if (!apiKey) return;
        loadCosts();
    }, [apiKey, days]);

    async function loadCosts() {
        setLoading(true);
        try {
            const result = await getCostSummary(apiKey, days);
            setData(result);
        } catch (e) {
            console.error("Load costs error:", e);
        }
        setLoading(false);
    }

    return (
        <div className="app-layout">
            <Sidebar active="/costs" />
            <main className="main-content">
                <div className="page-header">
                    <h2>Cost Intelligence</h2>
                    <p>Track and analyze AI agent costs across agents, models, and time</p>
                </div>

                <ApiKeyBar apiKey={apiKey} setApiKey={setApiKey} />

                {apiKey && loading && (
                    <div className="loading"><div className="spinner" /> Loading cost data...</div>
                )}

                {apiKey && data && (
                    <>
                        {/* ── Period Selector ──────────────────── */}
                        <div style={{ display: "flex", gap: "8px", marginBottom: "20px" }}>
                            {[7, 14, 30, 90].map((d) => (
                                <button
                                    key={d}
                                    className={`btn ${days === d ? "btn-primary" : "btn-ghost"}`}
                                    onClick={() => setDays(d)}
                                >
                                    {d}d
                                </button>
                            ))}
                        </div>

                        {/* ── Summary Stats ────────────────────── */}
                        <div className="card-grid card-grid-4">
                            <div className="card stat-card green">
                                <div className="stat-label">Total Cost</div>
                                <div className="stat-value">${(data.summary?.total_cost ?? 0).toFixed(4)}</div>
                                <div className="stat-change">Last {days} days</div>
                            </div>
                            <div className="card stat-card blue">
                                <div className="stat-label">Total Tokens</div>
                                <div className="stat-value">{(data.summary?.total_tokens ?? 0).toLocaleString()}</div>
                            </div>
                            <div className="card stat-card purple">
                                <div className="stat-label">Total Runs</div>
                                <div className="stat-value">{data.summary?.total_runs ?? 0}</div>
                            </div>
                            <div className="card stat-card amber">
                                <div className="stat-label">Avg Cost / Run</div>
                                <div className="stat-value">${(data.summary?.avg_cost_per_run ?? 0).toFixed(4)}</div>
                            </div>
                        </div>

                        {/* ── Cost by Agent ─────────────────────── */}
                        <div className="card-grid card-grid-2">
                            <div className="card">
                                <h3 style={{ fontSize: "15px", fontWeight: 600, marginBottom: "16px" }}>
                                    💰 Cost by Agent
                                </h3>
                                {(data.by_agent || []).length === 0 ? (
                                    <div className="empty-state" style={{ padding: "20px" }}>
                                        <p>No data available</p>
                                    </div>
                                ) : (
                                    <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                                        {data.by_agent.map((agent: any) => {
                                            const maxCost = Math.max(...data.by_agent.map((a: any) => a.total_cost));
                                            const pct = (agent.total_cost / maxCost) * 100;
                                            return (
                                                <div key={agent.agent_name}>
                                                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
                                                        <span style={{ fontSize: "13px", fontWeight: 500 }}>{agent.agent_name}</span>
                                                        <span style={{ fontSize: "13px", color: "var(--accent-green)" }}>
                                                            ${agent.total_cost.toFixed(4)}
                                                        </span>
                                                    </div>
                                                    <div
                                                        style={{
                                                            height: "6px",
                                                            borderRadius: "3px",
                                                            background: "var(--bg-glass)",
                                                            overflow: "hidden",
                                                        }}
                                                    >
                                                        <div
                                                            style={{
                                                                height: "100%",
                                                                width: `${pct}%`,
                                                                borderRadius: "3px",
                                                                background: "linear-gradient(90deg, var(--accent-purple), var(--accent-blue))",
                                                            }}
                                                        />
                                                    </div>
                                                    <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "2px" }}>
                                                        {agent.run_count} runs · {agent.total_tokens.toLocaleString()} tokens · avg ${agent.avg_cost_per_run.toFixed(4)}/run
                                                    </div>
                                                </div>
                                            );
                                        })}
                                    </div>
                                )}
                            </div>

                            {/* ── Cost by Model ───────────────────── */}
                            <div className="card">
                                <h3 style={{ fontSize: "15px", fontWeight: 600, marginBottom: "16px" }}>
                                    🤖 Cost by Model
                                </h3>
                                {(data.by_model || []).length === 0 ? (
                                    <div className="empty-state" style={{ padding: "20px" }}>
                                        <p>No data available</p>
                                    </div>
                                ) : (
                                    <table className="data-table">
                                        <thead>
                                            <tr>
                                                <th>Model</th>
                                                <th>Cost</th>
                                                <th>Tokens</th>
                                                <th>Calls</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {data.by_model.map((m: any) => (
                                                <tr key={m.model}>
                                                    <td>{m.model}</td>
                                                    <td style={{ color: "var(--accent-green)" }}>${m.total_cost.toFixed(4)}</td>
                                                    <td>{m.total_tokens.toLocaleString()}</td>
                                                    <td>{m.call_count}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                )}
                            </div>
                        </div>

                        {/* ── Cost Spikes ──────────────────────── */}
                        {data.spikes && data.spikes.length > 0 && (
                            <div className="card" style={{ marginTop: "20px" }}>
                                <h3 style={{ fontSize: "15px", fontWeight: 600, marginBottom: "16px" }}>
                                    🚨 Cost Spikes
                                </h3>
                                <table className="data-table">
                                    <thead>
                                        <tr>
                                            <th>Agent</th>
                                            <th>Cost</th>
                                            <th>Avg Cost</th>
                                            <th>Deviation</th>
                                            <th>Occurred</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {data.spikes.map((spike: any) => (
                                            <tr key={spike.run_id}>
                                                <td>{spike.agent_name}</td>
                                                <td style={{ color: "var(--accent-red)" }}>${spike.cost.toFixed(4)}</td>
                                                <td>${spike.avg_cost.toFixed(4)}</td>
                                                <td>{spike.deviation.toFixed(1)}x</td>
                                                <td>{new Date(spike.occurred_at).toLocaleString()}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </>
                )}
            </main>
        </div>
    );
}
