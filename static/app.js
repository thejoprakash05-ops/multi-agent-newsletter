"use strict";

// ── Category tabs ─────────────────────────────────────────────────────────────
const CATEGORIES = [
    { id: "all",           label: "All" },
    { id: "tech",          label: "Tech" },
    { id: "business",      label: "Business" },
    { id: "investment",    label: "Investment" },
    { id: "gold",          label: "Gold" },
    { id: "health",        label: "Health" },
    { id: "startups",      label: "Startups" },
    { id: "cricket",       label: "Cricket" },
    { id: "tennis",        label: "Tennis" },
    { id: "eda",           label: "EDA" },
    { id: "semiconductor", label: "Semiconductor" },
    { id: "saved",         label: "★ Saved" },
];

// Must match REFRESH_TIMES in config.py
const REFRESH_TIMES = [
    { h: 9,  m: 0 },
    { h: 13, m: 0 },
    { h: 18, m: 0 },
];

const CATEGORY_STYLES = {
    tech:          { accent: "#3b82f6", bg: "#dbeafe" },
    business:      { accent: "#10b981", bg: "#d1fae5" },
    investment:    { accent: "#f59e0b", bg: "#fef3c7" },
    gold:          { accent: "#d97706", bg: "#fff7ed" },
    health:        { accent: "#06b6d4", bg: "#cffafe" },
    startups:      { accent: "#8b5cf6", bg: "#ede9fe" },
    cricket:       { accent: "#16a34a", bg: "#dcfce7" },
    tennis:        { accent: "#0891b2", bg: "#e0f2fe" },
    eda:           { accent: "#7c3aed", bg: "#f5f3ff" },
    semiconductor: { accent: "#dc2626", bg: "#fee2e2" },
    world:         { accent: "#f59e0b", bg: "#fef3c7" },
    science:       { accent: "#8b5cf6", bg: "#ede9fe" },
    politics:      { accent: "#ef4444", bg: "#fee2e2" },
    other:         { accent: "#6b7280", bg: "#f1f5f9" },
};

const MAX_PER_TAB = 12;   // must match MAX_PER_CATEGORY in config.py

let currentUpdatedAt = null;
let allHeadlines     = [];
let currentCategory  = "all";
let searchQuery      = "";

// ── Helpers ───────────────────────────────────────────────────────────────────

function getCategoryStyle(category) {
    const key = (category || "other").toLowerCase().split(/[|\/]/)[0].trim();
    return CATEGORY_STYLES[key] || CATEGORY_STYLES.other;
}

function matchesCategory(category, tabId) {
    if (tabId === "all") return true;
    return (category || "other").toLowerCase().trim() === tabId.toLowerCase().trim();
}

function getNextRefreshTime() {
    const now = new Date();
    for (const t of REFRESH_TIMES) {
        const candidate = new Date(now);
        candidate.setHours(t.h, t.m, 0, 0);
        if (candidate > now) return candidate;
    }
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
    ["status-loading", "status-refreshing", "status-error",
     "status-empty", "status-no-cat", "status-no-saved", "headlines-grid"]
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

// ── Saved articles (localStorage) ────────────────────────────────────────────

function getSaved() {
    try { return JSON.parse(localStorage.getItem("savedArticles") || "{}"); }
    catch { return {}; }
}

function isSaved(link) {
    return !!getSaved()[link];
}

function setSaved(saved) {
    localStorage.setItem("savedArticles", JSON.stringify(saved));
}

function saveArticle(article) {
    const saved = getSaved();
    saved[article.link] = article;
    setSaved(saved);
}

function unsaveArticle(link) {
    const saved = getSaved();
    delete saved[link];
    setSaved(saved);
}

function toggleSave(link, article) {
    if (isSaved(link)) {
        unsaveArticle(link);
        return false;
    } else {
        if (article) saveArticle(article);
        return true;
    }
}

// ── Category tabs ─────────────────────────────────────────────────────────────

function renderTabs() {
    const nav = document.getElementById("category-tabs");
    nav.innerHTML = "";
    CATEGORIES.forEach(cat => {
        const btn = document.createElement("button");
        btn.className = "tab-btn"
            + (cat.id === currentCategory ? " active" : "")
            + (cat.id === "saved" ? " tab-saved" : "");
        btn.textContent = cat.label;
        btn.dataset.id  = cat.id;
        btn.addEventListener("click", () => selectCategory(cat.id));
        nav.appendChild(btn);
    });
}

function selectCategory(id) {
    currentCategory = id;
    document.querySelectorAll(".tab-btn").forEach(btn => {
        btn.classList.toggle("active", btn.dataset.id === id);
    });
    filterAndRender();
}

// ── Search ────────────────────────────────────────────────────────────────────

function onSearch(value) {
    searchQuery = value.trim();
    document.getElementById("search-clear").classList.toggle("hidden", !searchQuery);
    filterAndRender();
}

function clearSearch() {
    searchQuery = "";
    document.getElementById("search-input").value = "";
    document.getElementById("search-clear").classList.add("hidden");
    filterAndRender();
}

// ── Render ────────────────────────────────────────────────────────────────────

function filterAndRender() {
    // Pick source pool
    let pool = currentCategory === "saved"
        ? Object.values(getSaved())
        : allHeadlines.filter(h => matchesCategory(h.category, currentCategory));

    // Apply search
    if (searchQuery) {
        const q = searchQuery.toLowerCase();
        pool = pool.filter(h =>
            (h.title  || "").toLowerCase().includes(q) ||
            (h.source || "").toLowerCase().includes(q) ||
            (h.why    || "").toLowerCase().includes(q)
        );
    }

    const filtered = pool
        .sort((a, b) => (a.rank || 0) - (b.rank || 0))
        .slice(0, MAX_PER_TAB);

    if (!filtered.length) {
        if (currentCategory === "saved" && !searchQuery) {
            setStatus("status-no-saved");
        } else {
            const msg = searchQuery
                ? `No results for &ldquo;${escapeHtml(searchQuery)}&rdquo;`
                : "No stories in this category yet &mdash; try &ldquo;Refresh Now&rdquo; or pick another tab.";
            document.getElementById("status-no-cat-msg").innerHTML = msg;
            setStatus("status-no-cat");
        }
        return;
    }

    const grid = document.getElementById("headlines-grid");
    grid.innerHTML = "";
    filtered.forEach(h => {
        const style = getCategoryStyle(h.category);
        const card  = document.createElement("article");
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
                <div class="card-actions">
                    <button class="star-btn" aria-label="Save article"></button>
                    ${h.link ? `<a href="${escapeHtml(h.link)}" class="read-link" target="_blank" rel="noopener">Read more &rarr;</a>` : ""}
                </div>
            </div>
        `;

        // Wire up star button without inline handlers
        const starBtn = card.querySelector(".star-btn");
        const updateStar = () => {
            const saved = isSaved(h.link);
            starBtn.textContent = saved ? "★" : "☆";
            starBtn.title       = saved ? "Unsave" : "Save for later";
            starBtn.classList.toggle("saved", saved);
        };
        updateStar();
        starBtn.addEventListener("click", () => {
            toggleSave(h.link, h);
            updateStar();
            // Remove card immediately when unsaving inside the Saved tab
            if (currentCategory === "saved" && !isSaved(h.link)) filterAndRender();
        });

        grid.appendChild(card);
    });
    setStatus("headlines-grid");
}

function renderHeadlines(data) {
    const { updated_at, headlines } = data;
    allHeadlines     = headlines || [];
    currentUpdatedAt = updated_at;
    updateMeta(updated_at);
    filterAndRender();
}

// ── API calls ─────────────────────────────────────────────────────────────────

async function loadHeadlines() {
    try {
        const res = await fetch("/api/headlines");
        if (!res.ok) throw new Error("HTTP " + res.status);
        renderHeadlines(await res.json());
    } catch (err) {
        console.error("loadHeadlines:", err);
        document.getElementById("error-msg").textContent = err.message;
        setStatus("status-error");
    }
}

async function manualRefresh() {
    const btn  = document.getElementById("refresh-btn");
    const icon = document.getElementById("refresh-icon");
    btn.disabled = true;
    icon.classList.add("spinning");
    setStatus("status-refreshing");

    try {
        const res  = await fetch("/api/refresh", { method: "POST" });
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

// ── Init ──────────────────────────────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", () => {
    renderTabs();
    setStatus("status-loading");
    updateMeta(null);
    loadHeadlines();

    const searchInput = document.getElementById("search-input");
    searchInput.addEventListener("input",  e => onSearch(e.target.value));
    searchInput.addEventListener("keydown", e => { if (e.key === "Escape") clearSearch(); });
    document.getElementById("search-clear").addEventListener("click", clearSearch);

    setInterval(pollForUpdates, 60_000);
    setInterval(() => updateMeta(currentUpdatedAt), 30_000);
});
