"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { getRuns, getCostSummary, getAlerts } from "@/lib/api";

/* ── Sidebar Navigation ─────────────────────────── */
function Sidebar({ active }: { active: string }) {
    const links = [
        { href: "/", label: "Dashboard", icon: "📊" },
        { href: "/runs", label: "Runs", icon: "🔄" },
        { href: "/costs", label: "Costs", icon: "💰" },
        { href: "/evaluations", label: "Quality", icon: "✅" },
        { href: "/guardrails", label: "Guardrails", icon: "🛡️" },
    ];

    return (
        <aside className="sidebar">
            <div className="sidebar-logo">
                <div className="logo-icon">A</div>
                <div>
                    <h1>Agent Control Room</h1>
                    <span>Reliability Platform</span>
                </div>
            </div>
            <nav className="sidebar-nav">
                {links.map((link) => (
                    <Link
                        key={link.href}
                        href={link.href}
                        className={`nav-link ${active === link.href ? "active" : ""}`}
                    >
                        <span>{link.icon}</span>
                        {link.label}
                    </Link>
                ))}
            </nav>
            <div style={{ padding: "12px", fontSize: "11px", color: "var(--text-muted)" }}>
                v0.1.0 — Agent Control Room
            </div>
        </aside>
    );
}

export { Sidebar };

/* ── API Key Bar ────────────────────────────────── */
function ApiKeyBar({
    apiKey,
    setApiKey,
}: {
    apiKey: string;
    setApiKey: (k: string) => void;
}) {
    return (
        <div className="api-key-bar">
            <label>🔑 API Key</label>
            <input
                type="text"
                placeholder="Paste your API key (from backend console)..."
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
            />
        </div>
    );
}

export { ApiKeyBar };

/* ── Dashboard Page ─────────────────────────────── */
export default function DashboardPage() {
    const [apiKey, setApiKey] = useState("");
    const [stats, setStats] = useState<any>(null);
    const [recentRuns, setRecentRuns] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (!apiKey) return;
        loadDashboard();
    }, [apiKey]);

    async function loadDashboard() {
        setLoading(true);
        try {
            const [runsData, costData] = await Promise.all([
                getRuns({ apiKey, page: 1, pageSize: 5 }).catch(() => null),
                getCostSummary(apiKey, 30).catch(() => null),
            ]);

            if (runsData) setRecentRuns(runsData.runs || []);
            if (costData) setStats(costData.summary);
        } catch (e) {
            console.error("Dashboard load error:", e);
        }
        setLoading(false);
    }

    return (
        <div className="app-layout">
            <Sidebar active="/" />
            <main className="main-content">
                <div className="page-header">
                    <h2>Dashboard</h2>
                    <p>Reliability overview for your AI agents</p>
                </div>

                <ApiKeyBar apiKey={apiKey} setApiKey={setApiKey} />

                {!apiKey && (
                    <div className="empty-state">
                        <h3>Enter your API key to get started</h3>
                        <p>
                            Run the backend with <code>docker-compose up</code> and copy the
                            API key from the console output.
                        </p>
                    </div>
                )}

                {apiKey && loading && (
                    <div className="loading">
                        <div className="spinner" />
                        Loading dashboard...
                    </div>
                )}

                {apiKey && !loading && (
                    <>
                        {/* ── Stat Cards ─────────────────────── */}
                        <div className="card-grid card-grid-4">
                            <div className="card stat-card purple">
                                <div className="stat-label">Total Runs</div>
                                <div className="stat-value">{stats?.total_runs ?? "—"}</div>
                                <div className="stat-change">Last 30 days</div>
                            </div>
                            <div className="card stat-card green">
                                <div className="stat-label">Total Cost</div>
                                <div className="stat-value">
                                    ${(stats?.total_cost ?? 0).toFixed(4)}
                                </div>
                                <div className="stat-change">Last 30 days</div>
                            </div>
                            <div className="card stat-card blue">
                                <div className="stat-label">Total Tokens</div>
                                <div className="stat-value">
                                    {(stats?.total_tokens ?? 0).toLocaleString()}
                                </div>
                                <div className="stat-change">Last 30 days</div>
                            </div>
                            <div className="card stat-card amber">
                                <div className="stat-label">Avg Cost / Run</div>
                                <div className="stat-value">
                                    ${(stats?.avg_cost_per_run ?? 0).toFixed(4)}
                                </div>
                                <div className="stat-change">Last 30 days</div>
                            </div>
                        </div>

                        {/* ── Recent Runs ─────────────────────── */}
                        <div className="card">
                            <div
                                style={{
                                    display: "flex",
                                    justifyContent: "space-between",
                                    alignItems: "center",
                                    marginBottom: "16px",
                                }}
                            >
                                <h3 style={{ fontSize: "16px", fontWeight: 600 }}>
                                    Recent Runs
                                </h3>
                                <Link href="/runs" className="btn btn-ghost">
                                    View All →
                                </Link>
                            </div>

                            {recentRuns.length === 0 ? (
                                <div className="empty-state">
                                    <h3>No runs yet</h3>
                                    <p>Run the demo agent to generate sample data.</p>
                                </div>
                            ) : (
                                <table className="data-table">
                                    <thead>
                                        <tr>
                                            <th>Agent</th>
                                            <th>Status</th>
                                            <th>Cost</th>
                                            <th>Tokens</th>
                                            <th>Spans</th>
                                            <th>Started</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {recentRuns.map((run: any) => (
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
                                                <td>${(run.total_cost ?? 0).toFixed(4)}</td>
                                                <td>{(run.total_tokens ?? 0).toLocaleString()}</td>
                                                <td>{run.total_spans ?? 0}</td>
                                                <td>
                                                    {run.started_at
                                                        ? new Date(run.started_at).toLocaleString()
                                                        : "—"}
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            )}
                        </div>
                    </>
                )}
            </main>
        </div>
    );
}
