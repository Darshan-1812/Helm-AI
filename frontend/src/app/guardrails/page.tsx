"use client";

import React, { useState, useEffect } from "react";
import { Sidebar, ApiKeyBar } from "../page";
import { getGuardrails, createGuardrail, getAlerts } from "@/lib/api";

export default function GuardrailsPage() {
    const [apiKey, setApiKey] = useState("");
    const [configs, setConfigs] = useState<any[]>([]);
    const [alerts, setAlerts] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);
    const [showForm, setShowForm] = useState(false);
    const [formData, setFormData] = useState({
        name: "",
        rule_type: "cost_limit",
        threshold: 1.0,
        action: "alert",
        enabled: true,
    });

    useEffect(() => {
        if (!apiKey) return;
        loadData();
    }, [apiKey]);

    async function loadData() {
        setLoading(true);
        try {
            const [configData, alertData] = await Promise.all([
                getGuardrails(apiKey).catch(() => []),
                getAlerts(apiKey).catch(() => []),
            ]);
            setConfigs(configData || []);
            setAlerts(alertData || []);
        } catch (e) {
            console.error("Load guardrails error:", e);
        }
        setLoading(false);
    }

    async function handleCreate() {
        try {
            await createGuardrail(apiKey, formData);
            setShowForm(false);
            setFormData({ name: "", rule_type: "cost_limit", threshold: 1.0, action: "alert", enabled: true });
            loadData();
        } catch (e) {
            console.error("Create guardrail error:", e);
        }
    }

    const ruleTypeLabels: Record<string, string> = {
        cost_limit: "💰 Cost Limit",
        loop_detection: "🔄 Loop Detection",
        latency_budget: "⏱ Latency Budget",
        quality_gate: "✅ Quality Gate",
        token_limit: "📊 Token Limit",
    };

    const actionColors: Record<string, string> = {
        alert: "var(--accent-amber)",
        block: "var(--accent-red)",
        kill: "var(--accent-red)",
    };

    return (
        <div className="app-layout">
            <Sidebar active="/guardrails" />
            <main className="main-content">
                <div className="page-header">
                    <h2>Guardrails</h2>
                    <p>Configure reliability rules and view triggered alerts</p>
                </div>

                <ApiKeyBar apiKey={apiKey} setApiKey={setApiKey} />

                {apiKey && loading && (
                    <div className="loading"><div className="spinner" /> Loading guardrails...</div>
                )}

                {apiKey && !loading && (
                    <>
                        {/* ── Guardrail Rules ──────────────────── */}
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
                            <h3 style={{ fontSize: "16px", fontWeight: 600 }}>🛡️ Active Rules</h3>
                            <button className="btn btn-primary" onClick={() => setShowForm(!showForm)}>
                                {showForm ? "Cancel" : "+ Add Rule"}
                            </button>
                        </div>

                        {showForm && (
                            <div className="card" style={{ marginBottom: "20px", display: "flex", flexDirection: "column", gap: "12px" }}>
                                <input
                                    type="text"
                                    placeholder="Rule name..."
                                    value={formData.name}
                                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                    style={{ background: "rgba(0,0,0,0.3)", border: "1px solid var(--border-color)", borderRadius: "6px", padding: "8px 12px", color: "var(--text-primary)", fontSize: "13px" }}
                                />
                                <div style={{ display: "flex", gap: "12px" }}>
                                    <select
                                        value={formData.rule_type}
                                        onChange={(e) => setFormData({ ...formData, rule_type: e.target.value })}
                                        style={{ background: "rgba(0,0,0,0.3)", border: "1px solid var(--border-color)", borderRadius: "6px", padding: "6px 10px", color: "var(--text-primary)", fontSize: "13px", flex: 1 }}
                                    >
                                        <option value="cost_limit">Cost Limit ($)</option>
                                        <option value="loop_detection">Loop Detection (max iterations)</option>
                                        <option value="latency_budget">Latency Budget (ms)</option>
                                        <option value="quality_gate">Quality Gate (min score)</option>
                                        <option value="token_limit">Token Limit</option>
                                    </select>
                                    <input
                                        type="number"
                                        step="0.01"
                                        value={formData.threshold}
                                        onChange={(e) => setFormData({ ...formData, threshold: parseFloat(e.target.value) })}
                                        style={{ background: "rgba(0,0,0,0.3)", border: "1px solid var(--border-color)", borderRadius: "6px", padding: "6px 10px", color: "var(--text-primary)", fontSize: "13px", width: "120px" }}
                                    />
                                    <select
                                        value={formData.action}
                                        onChange={(e) => setFormData({ ...formData, action: e.target.value })}
                                        style={{ background: "rgba(0,0,0,0.3)", border: "1px solid var(--border-color)", borderRadius: "6px", padding: "6px 10px", color: "var(--text-primary)", fontSize: "13px" }}
                                    >
                                        <option value="alert">Alert</option>
                                        <option value="block">Block</option>
                                        <option value="kill">Kill</option>
                                    </select>
                                </div>
                                <button className="btn btn-primary" onClick={handleCreate} style={{ alignSelf: "flex-end" }}>
                                    Create Rule
                                </button>
                            </div>
                        )}

                        {configs.length === 0 && !showForm ? (
                            <div className="card" style={{ marginBottom: "24px" }}>
                                <div className="empty-state">
                                    <h3>No guardrails configured</h3>
                                    <p>Add rules to protect your agents from cost overruns, infinite loops, and low quality.</p>
                                </div>
                            </div>
                        ) : (
                            <div className="card-grid card-grid-3" style={{ marginBottom: "24px" }}>
                                {configs.map((config: any) => (
                                    <div className="card" key={config.id}>
                                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                                            <span style={{ fontSize: "14px", fontWeight: 600 }}>{config.name}</span>
                                            <span
                                                className="badge"
                                                style={{
                                                    background: config.enabled ? "rgba(16,185,129,0.1)" : "rgba(255,255,255,0.05)",
                                                    color: config.enabled ? "var(--accent-green)" : "var(--text-muted)",
                                                    border: `1px solid ${config.enabled ? "rgba(16,185,129,0.2)" : "var(--border-color)"}`,
                                                }}
                                            >
                                                {config.enabled ? "Active" : "Disabled"}
                                            </span>
                                        </div>
                                        <div style={{ fontSize: "12px", color: "var(--text-muted)", marginBottom: "8px" }}>
                                            {ruleTypeLabels[config.rule_type] || config.rule_type}
                                        </div>
                                        <div style={{ display: "flex", justifyContent: "space-between", fontSize: "13px" }}>
                                            <span>Threshold: <b>{config.threshold}</b></span>
                                            <span style={{ color: actionColors[config.action] || "var(--text-secondary)" }}>
                                                Action: {config.action.toUpperCase()}
                                            </span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}

                        {/* ── Alerts ──────────────────────────── */}
                        <h3 style={{ fontSize: "16px", fontWeight: 600, marginBottom: "12px" }}>🚨 Alerts</h3>
                        <div className="card">
                            {alerts.length === 0 ? (
                                <div className="empty-state" style={{ padding: "30px" }}>
                                    <h3>No alerts</h3>
                                    <p>Alerts will appear here when guardrail rules are triggered.</p>
                                </div>
                            ) : (
                                <table className="data-table">
                                    <thead>
                                        <tr>
                                            <th>Type</th>
                                            <th>Severity</th>
                                            <th>Message</th>
                                            <th>Status</th>
                                            <th>Created</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {alerts.map((alert: any) => (
                                            <tr key={alert.id}>
                                                <td>{alert.alert_type}</td>
                                                <td>
                                                    <span className={`badge ${alert.severity === "critical" ? "failed" : alert.severity === "warning" ? "timeout" : "completed"}`}>
                                                        {alert.severity}
                                                    </span>
                                                </td>
                                                <td style={{ maxWidth: "400px", overflow: "hidden", textOverflow: "ellipsis" }}>
                                                    {alert.message}
                                                </td>
                                                <td>{alert.is_resolved ? "✅ Resolved" : "⚠️ Active"}</td>
                                                <td>{alert.created_at ? new Date(alert.created_at).toLocaleString() : "—"}</td>
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
