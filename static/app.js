"use strict";

// Must match REFRESH_TIMES in config.py
const REFRESH_TIMES = [
    { h: 9,  m: 0 },
    { h: 13, m: 0 },
    { h: 18, m: 0 },
];

const CATEGORY_STYLES = {
    tech:     { accent: "#3b82f6", bg: "#dbeafe" },
    business: { accent: "#10b981", bg: "#d1fae5" },
    world:    { accent: "#f59e0b", bg: "#fef3c7" },
    science:  { accent: "#8b5cf6", bg: "#ede9fe" },
    health:   { accent: "#06b6d4", bg: "#cffafe" },
    politics: { accent: "#ef4444", bg: "#fee2e2" },
    other:    { accent: "#6b7280", bg: "#f1f5f9" },
};

let currentUpdatedAt = null;

// ── Helpers ────────────────────────────────────────────────────

function getCategoryStyle(category) {
    const key = (category || "other").toLowerCase().split(/[|\/]/)[0].trim();
    return CATEGORY_STYLES[key] || CATEGORY_STYLES.other;
}

function getNextRefreshTime() {
    const now = new Date();
    for (const t of REFRESH_TIMES) {
        const candidate = new Date(now);
        candidate.setHours(t.h, t.m, 0, 0);
        if (candidate > now) return candidate;
    }
    // All today's refreshes have passed — next is tomorrow at 9 AM
    const tomorrow = new Date(now);
    tomorrow.setDate(tomorrow.getDate() + 1);
    tomorrow.setHours(9, 0, 0, 0);
    return tomorrow;
}

function formatDateTime(iso) {
    if (!iso) return "Never";
    return new Date(iso).toLocaleString(undefined, {
        month: "short", day: "numeric",
        hour: "2-digit", minute: "2-digit",
    });
}

function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str || "";
    return div.innerHTML;
}

function show(id) { document.getElementById(id).classList.remove("hidden"); }
function hide(id) { document.getElementById(id).classList.add("hidden"); }

function setStatus(activeId) {
    ["status-loading", "status-refreshing", "status-error", "status-empty", "headlines-grid"]
        .forEach(id => hide(id));
    show(activeId);
}

function updateMeta(updatedAt) {
    document.getElementById("last-updated").textContent = updatedAt
        ? "Updated " + formatDateTime(updatedAt)
        : "Not yet updated";
    document.getElementById("next-refresh").textContent =
        getNextRefreshTime().toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" });
}

// ── Render ─────────────────────────────────────────────────────

function renderHeadlines(data) {
    const { updated_at, headlines } = data;
    currentUpdatedAt = updated_at;
    updateMeta(updated_at);

    if (!headlines || headlines.length === 0) {
        setStatus("status-empty");
        return;
    }

    const grid = document.getElementById("headlines-grid");
    grid.innerHTML = "";

    headlines.forEach(h => {
        const style = getCategoryStyle(h.category);
        const card = document.createElement("article");
        card.className = "headline-card";
        card.style.setProperty("--card-accent",    style.accent);
        card.style.setProperty("--card-accent-bg", style.bg);
        card.innerHTML = `
            <div class="card-header">
                <div class="rank-badge">${h.rank}</div>
                <span class="category-pill">${escapeHtml(h.category || "Other")}</span>
            </div>
            <p class="card-title">${escapeHtml(h.title)}</p>
            ${h.why ? `<p class="card-why">${escapeHtml(h.why)}</p>` : ""}
            <div class="card-footer">
                <span class="source-tag">${escapeHtml(h.source || "")}</span>
                ${h.link ? `<a href="${escapeHtml(h.link)}" class="read-link" target="_blank" rel="noopener">Read more &rarr;</a>` : ""}
            </div>
        `;
        grid.appendChild(card);
    });

    setStatus("headlines-grid");
}

// ── API calls ──────────────────────────────────────────────────

async function loadHeadlines() {
    try {
        const res = await fetch("/api/headlines");
        if (!res.ok) throw new Error("HTTP " + res.status);
        const data = await res.json();
        renderHeadlines(data);
    } catch (err) {
        console.error("loadHeadlines:", err);
        document.getElementById("error-msg").textContent = err.message;
        setStatus("status-error");
    }
}

async function manualRefresh() {
    const btn = document.getElementById("refresh-btn");
    const icon = document.getElementById("refresh-icon");
    btn.disabled = true;
    icon.classList.add("spinning");
    setStatus("status-refreshing");

    try {
        const res = await fetch("/api/refresh", { method: "POST" });
        const data = await res.json();
        if (!res.ok || data.status === "error") throw new Error(data.message || "HTTP " + res.status);
        renderHeadlines(data);
    } catch (err) {
        console.error("manualRefresh:", err);
        document.getElementById("error-msg").textContent = err.message;
        setStatus("status-error");
    } finally {
        btn.disabled = false;
        icon.classList.remove("spinning");
    }
}

// Poll every 60 s to pick up scheduled background refreshes
async function pollForUpdates() {
    try {
        const res = await fetch("/api/headlines");
        if (!res.ok) return;
        const data = await res.json();
        if (data.updated_at && data.updated_at !== currentUpdatedAt) {
            renderHeadlines(data);
        }
    } catch (_) {}
}

// ── Init ───────────────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", () => {
    setStatus("status-loading");
    updateMeta(null);
    loadHeadlines();
    setInterval(pollForUpdates, 60_000);
    // Keep "Next refresh" clock accurate
    setInterval(() => updateMeta(currentUpdatedAt), 30_000);
});
