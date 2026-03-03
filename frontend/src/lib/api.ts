/**
 * Agent Control Room — Backend API Client
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
const API_KEY = process.env.NEXT_PUBLIC_API_KEY || "";

interface FetchOptions extends RequestInit {
    apiKey?: string;
}

async function apiFetch(path: string, options: FetchOptions = {}) {
    const { apiKey, ...fetchOptions } = options;
    const key = apiKey || API_KEY;

    const res = await fetch(`${API_BASE}${path}`, {
        ...fetchOptions,
        headers: {
            "Content-Type": "application/json",
            "X-API-Key": key,
            ...fetchOptions.headers,
        },
        cache: "no-store",
    });

    if (!res.ok) {
        const error = await res.text();
        throw new Error(`API Error ${res.status}: ${error}`);
    }

    return res.json();
}

// ── Runs ──────────────────────────────────────────────

export async function getRuns(params: {
    apiKey: string;
    page?: number;
    pageSize?: number;
    status?: string;
    agentName?: string;
}) {
    const query = new URLSearchParams();
    if (params.page) query.set("page", String(params.page));
    if (params.pageSize) query.set("page_size", String(params.pageSize));
    if (params.status) query.set("status", params.status);
    if (params.agentName) query.set("agent_name", params.agentName);

    return apiFetch(`/runs?${query.toString()}`, { apiKey: params.apiKey });
}

export async function getRun(runId: string, apiKey: string) {
    return apiFetch(`/runs/${runId}`, { apiKey });
}

// ── Costs ─────────────────────────────────────────────

export async function getCostSummary(apiKey: string, days: number = 30) {
    return apiFetch(`/costs/summary?days=${days}`, { apiKey });
}

export async function getCostByAgent(apiKey: string, days: number = 30) {
    return apiFetch(`/costs/by-agent?days=${days}`, { apiKey });
}

export async function getCostByModel(apiKey: string, days: number = 30) {
    return apiFetch(`/costs/by-model?days=${days}`, { apiKey });
}

// ── Evaluations ───────────────────────────────────────

export async function getEvaluations(params: {
    apiKey: string;
    page?: number;
    runId?: string;
}) {
    const query = new URLSearchParams();
    if (params.page) query.set("page", String(params.page));
    if (params.runId) query.set("run_id", params.runId);

    return apiFetch(`/evaluations?${query.toString()}`, { apiKey: params.apiKey });
}

export async function getEvalSummary(runId: string, apiKey: string) {
    return apiFetch(`/evaluations/summary/${runId}`, { apiKey });
}

// ── Guardrails ────────────────────────────────────────

export async function getGuardrails(apiKey: string) {
    return apiFetch("/guardrails/configs", { apiKey });
}

export async function createGuardrail(
    apiKey: string,
    data: {
        name: string;
        rule_type: string;
        threshold: number;
        action: string;
        enabled: boolean;
    }
) {
    return apiFetch("/guardrails/configs", {
        method: "POST",
        body: JSON.stringify(data),
        apiKey,
    });
}

export async function getAlerts(apiKey: string, resolved?: boolean) {
    const query = new URLSearchParams();
    if (resolved !== undefined) query.set("resolved", String(resolved));
    return apiFetch(`/guardrails/alerts?${query.toString()}`, { apiKey });
}

// ── Health ────────────────────────────────────────────

export async function healthCheck() {
    const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL?.replace("/api/v1", "") || "http://localhost:8000"}/health`
    );
    return res.json();
}
