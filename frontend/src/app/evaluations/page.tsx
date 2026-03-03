"use client";

import React, { useState, useEffect } from "react";
import { Sidebar, ApiKeyBar } from "../page";
import { getEvaluations } from "@/lib/api";

export default function EvaluationsPage() {
    const [apiKey, setApiKey] = useState("");
    const [evals, setEvals] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (!apiKey) return;
        loadEvals();
    }, [apiKey]);

    async function loadEvals() {
        setLoading(true);
        try {
            const data = await getEvaluations({ apiKey, page: 1 });
            setEvals(data.evaluations || []);
        } catch (e) {
            console.error("Load evals error:", e);
        }
        setLoading(false);
    }

    function scoreColor(score: number) {
        if (score >= 0.8) return "var(--accent-green)";
        if (score >= 0.5) return "var(--accent-amber)";
        return "var(--accent-red)";
    }

    return (
        <div className="app-layout">
            <Sidebar active="/evaluations" />
            <main className="main-content">
                <div className="page-header">
                    <h2>Quality Evaluation</h2>
                    <p>Monitor hallucination, faithfulness, correctness, and relevance scores</p>
                </div>

                <ApiKeyBar apiKey={apiKey} setApiKey={setApiKey} />

                {apiKey && loading && (
                    <div className="loading"><div className="spinner" /> Loading evaluations...</div>
                )}

                {apiKey && !loading && (
                    <div className="card">
                        {evals.length === 0 ? (
                            <div className="empty-state">
                                <h3>No evaluations yet</h3>
                                <p>Trigger evaluations via the API or wait for automatic quality scoring.</p>
                            </div>
                        ) : (
                            <table className="data-table">
                                <thead>
                                    <tr>
                                        <th>Type</th>
                                        <th>Score</th>
                                        <th>Label</th>
                                        <th>Reason</th>
                                        <th>Run</th>
                                        <th>Evaluated</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {evals.map((ev: any) => (
                                        <tr key={ev.id}>
                                            <td>
                                                <span className="span-kind agent" style={{ textTransform: "capitalize" }}>
                                                    {ev.eval_type}
                                                </span>
                                            </td>
                                            <td>
                                                <span style={{ color: scoreColor(ev.score), fontWeight: 700, fontSize: "15px" }}>
                                                    {(ev.score * 100).toFixed(0)}%
                                                </span>
                                            </td>
                                            <td>{ev.label || "—"}</td>
                                            <td style={{ maxWidth: "300px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                                                {ev.reason || "—"}
                                            </td>
                                            <td style={{ fontFamily: "monospace", fontSize: "11px" }}>
                                                {ev.run_id?.slice(0, 8)}...
                                            </td>
                                            <td>{ev.evaluated_at ? new Date(ev.evaluated_at).toLocaleString() : "—"}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        )}
                    </div>
                )}
            </main>
        </div>
    );
}
