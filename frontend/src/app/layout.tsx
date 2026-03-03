import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
    title: "Agent Control Room — Reliability Layer for AI Agents",
    description:
        "Full agent tracing, session recording & replay, cost intelligence, quality evaluation, and guardrails for autonomous AI agents.",
};

export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="en">
            <body>{children}</body>
        </html>
    );
}
