"use client";

import React from "react";
import Link from "next/link";

/* ── Sidebar ─────────────────────────────────────── */
export function Sidebar({ active }: { active: string }) {
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

/* ── API Key Bar ─────────────────────────────────── */
export function ApiKeyBar({
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

/* ── Stat Card ───────────────────────────────────── */
export function StatCard({
    label,
    value,
    subtitle,
    color = "purple",
}: {
    label: string;
    value: string | number;
    subtitle?: string;
    color?: "purple" | "blue" | "green" | "amber" | "red" | "cyan";
}) {
    return (
        <div className={`card stat-card ${color}`}>
            <div className="stat-label">{label}</div>
            <div className="stat-value">{value}</div>
            {subtitle && <div className="stat-change">{subtitle}</div>}
        </div>
    );
}

/* ── Status Badge ────────────────────────────────── */
export function StatusBadge({ status }: { status: string }) {
    return <span className={`badge ${status}`}>{status}</span>;
}

/* ── Span Kind Badge ─────────────────────────────── */
export function SpanKindBadge({ kind }: { kind: string }) {
    return <span className={`span-kind ${kind}`}>{kind}</span>;
}

/* ── Loading Spinner ─────────────────────────────── */
export function Loading({ text = "Loading..." }: { text?: string }) {
    return (
        <div className="loading">
            <div className="spinner" />
            {text}
        </div>
    );
}

/* ── Empty State ─────────────────────────────────── */
export function EmptyState({
    title,
    description,
}: {
    title: string;
    description: string;
}) {
    return (
        <div className="empty-state">
            <h3>{title}</h3>
            <p>{description}</p>
        </div>
    );
}
