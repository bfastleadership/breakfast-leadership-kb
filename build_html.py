#!/usr/bin/env python3
"""Build index.html knowledge base from episodes_tagged.json."""

import json

with open("episodes_tagged.json", encoding="utf-8") as f:
    episodes = json.load(f)

episodes_json = json.dumps(episodes, ensure_ascii=False)

QA_PROXY_URL = "https://breakfast-leadership-qa.michael-4ac.workers.dev"

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Breakfast Leadership Show — Episode Knowledge Base</title>
<script>window.QA_PROXY_URL = '{QA_PROXY_URL}';</script>
<style>
  :root {{
    --bg: #f8f9fa;
    --surface: #ffffff;
    --border: #e2e6ea;
    --primary: #1a3557;
    --accent: #c8973a;
    --accent2: #2e6da4;
    --text: #1c2b3a;
    --muted: #6c7a89;
    --tag-bg: #eef2f7;
    --tag-text: #2e4a6b;
    --radius: 8px;
    --shadow: 0 1px 4px rgba(0,0,0,0.08);
    --shadow-lg: 0 4px 20px rgba(0,0,0,0.10);
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: var(--bg); color: var(--text); min-height: 100vh; }}

  /* HEADER */
  header {{ background: var(--primary); color: #fff; padding: 20px 28px; display: flex; align-items: center; gap: 16px; }}
  header h1 {{ font-size: 1.25rem; font-weight: 700; letter-spacing: -0.01em; }}
  header span {{ font-size: 0.85rem; opacity: 0.7; margin-left: auto; white-space: nowrap; }}

  /* LAYOUT */
  .layout {{ display: grid; grid-template-columns: 240px 1fr; gap: 0; max-width: 1400px; margin: 0 auto; }}

  /* SIDEBAR */
  .sidebar {{ background: var(--surface); border-right: 1px solid var(--border); padding: 20px 0; position: sticky; top: 0; height: 100vh; overflow-y: auto; }}
  .sidebar h2 {{ font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.08em; color: var(--muted); padding: 0 20px 8px; border-bottom: 1px solid var(--border); margin-bottom: 8px; }}
  .tag-item {{ display: flex; align-items: center; gap: 8px; padding: 7px 20px; cursor: pointer; font-size: 0.85rem; color: var(--text); border-left: 3px solid transparent; transition: all 0.15s; user-select: none; }}
  .tag-item:hover {{ background: #f0f4f8; }}
  .tag-item.active {{ border-left-color: var(--accent); background: #fdf6ec; color: var(--primary); font-weight: 600; }}
  .tag-item .count {{ margin-left: auto; font-size: 0.75rem; color: var(--muted); }}
  .tag-item.all-tags {{ font-weight: 600; color: var(--primary); }}

  /* MAIN */
  main {{ padding: 24px 28px; max-height: 100vh; overflow-y: auto; }}

  /* Q&A SECTION */
  .qa-section {{ background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 20px 24px; margin-bottom: 24px; box-shadow: var(--shadow-lg); }}
  .qa-label {{ font-size: 0.7rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: var(--accent); margin-bottom: 8px; }}
  .qa-title {{ font-size: 1.05rem; font-weight: 700; color: var(--primary); margin-bottom: 12px; }}
  .qa-row {{ display: flex; gap: 10px; }}
  #qa-input {{ flex: 1; border: 1.5px solid var(--border); border-radius: var(--radius); padding: 10px 14px; font-size: 0.9rem; color: var(--text); outline: none; transition: border-color 0.15s; }}
  #qa-input:focus {{ border-color: var(--accent2); }}
  #qa-btn {{ background: var(--primary); color: #fff; border: none; border-radius: var(--radius); padding: 10px 20px; font-size: 0.875rem; font-weight: 600; cursor: pointer; white-space: nowrap; transition: background 0.15s; }}
  #qa-btn:hover {{ background: #254a78; }}
  #qa-btn:disabled {{ background: #aab4c0; cursor: not-allowed; }}
  .qa-examples {{ font-size: 0.78rem; color: var(--muted); margin-top: 7px; }}
  .qa-examples span {{ cursor: pointer; color: var(--accent2); text-decoration: underline; text-decoration-style: dotted; }}
  .qa-examples span:hover {{ color: var(--primary); }}

  /* LOADING */
  .loading {{ display: none; align-items: center; gap: 10px; padding: 12px 0; color: var(--muted); font-size: 0.875rem; }}
  .loading.show {{ display: flex; }}
  .spinner {{ width: 18px; height: 18px; border: 2px solid var(--border); border-top-color: var(--accent); border-radius: 50%; animation: spin 0.7s linear infinite; }}
  @keyframes spin {{ to {{ transform: rotate(360deg); }} }}

  /* QA RESULTS */
  #qa-results {{ margin-top: 16px; }}
  .qa-result-card {{ background: #f4f8ff; border: 1px solid #d0dff5; border-radius: var(--radius); padding: 14px 16px; margin-bottom: 10px; }}
  .qa-rank {{ display: inline-block; background: var(--accent); color: #fff; font-size: 0.7rem; font-weight: 700; border-radius: 4px; padding: 2px 6px; margin-right: 8px; }}
  .qa-result-title a {{ font-weight: 700; color: var(--primary); font-size: 0.95rem; text-decoration: none; }}
  .qa-result-title a:hover {{ text-decoration: underline; }}
  .qa-meta {{ font-size: 0.78rem; color: var(--muted); margin: 4px 0 6px; }}
  .qa-relevance {{ font-size: 0.83rem; color: #3d5a7e; font-style: italic; border-left: 3px solid var(--accent); padding-left: 8px; margin-top: 6px; }}
  .qa-error {{ background: #fff3cd; border: 1px solid #ffc107; border-radius: var(--radius); padding: 12px 16px; font-size: 0.875rem; color: #7a5800; }}

  /* FILTER BAR */
  .filter-bar {{ display: flex; align-items: center; gap: 10px; margin-bottom: 16px; }}
  #search-input {{ flex: 1; border: 1.5px solid var(--border); border-radius: var(--radius); padding: 9px 14px; font-size: 0.9rem; color: var(--text); outline: none; }}
  #search-input:focus {{ border-color: var(--accent2); }}
  .sort-select {{ border: 1.5px solid var(--border); border-radius: var(--radius); padding: 9px 10px; font-size: 0.85rem; color: var(--text); background: var(--surface); cursor: pointer; outline: none; }}
  .result-count {{ font-size: 0.8rem; color: var(--muted); white-space: nowrap; }}

  /* EPISODE LIST */
  #episode-list {{ display: flex; flex-direction: column; gap: 10px; }}
  .ep-card {{ background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 14px 16px; transition: box-shadow 0.15s; }}
  .ep-card:hover {{ box-shadow: var(--shadow-lg); }}
  .ep-header {{ display: flex; align-items: flex-start; gap: 10px; }}
  .ep-num {{ font-size: 0.72rem; color: var(--muted); white-space: nowrap; padding-top: 2px; }}
  .ep-title a {{ font-weight: 700; color: var(--primary); font-size: 0.95rem; text-decoration: none; line-height: 1.35; }}
  .ep-title a:hover {{ text-decoration: underline; }}
  .ep-meta {{ display: flex; flex-wrap: wrap; gap: 6px; align-items: center; margin: 6px 0 8px; font-size: 0.78rem; color: var(--muted); }}
  .ep-meta .guest {{ color: var(--accent2); font-weight: 600; }}
  .ep-tags {{ display: flex; flex-wrap: wrap; gap: 5px; }}
  .tag-pill {{ display: inline-block; background: var(--tag-bg); color: var(--tag-text); font-size: 0.72rem; font-weight: 600; border-radius: 20px; padding: 3px 9px; cursor: pointer; transition: background 0.1s; }}
  .tag-pill:hover {{ background: #d6e4f4; }}
  .ep-desc {{ font-size: 0.8rem; color: var(--muted); margin-top: 8px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }}
  .no-results {{ text-align: center; padding: 48px; color: var(--muted); font-size: 0.95rem; }}

  /* MOBILE */
  @media (max-width: 768px) {{
    .layout {{ grid-template-columns: 1fr; }}
    .sidebar {{ position: static; height: auto; max-height: 220px; border-right: none; border-bottom: 1px solid var(--border); }}
    main {{ padding: 16px; max-height: none; }}
    header h1 {{ font-size: 1rem; }}
    header span {{ display: none; }}
    .qa-row {{ flex-direction: column; }}
    #qa-btn {{ width: 100%; }}
  }}
</style>
</head>
<body>

<header>
  <div>
    <div style="font-size:0.72rem;text-transform:uppercase;letter-spacing:0.08em;opacity:0.6;margin-bottom:3px;">Podcast Knowledge Base</div>
    <h1>Breakfast Leadership Show</h1>
  </div>
  <span id="ep-total-header"></span>
</header>

<div class="layout">

  <!-- SIDEBAR: Tag Filter -->
  <aside class="sidebar">
    <h2>Filter by Topic</h2>
    <div id="tag-list"></div>
  </aside>

  <!-- MAIN CONTENT -->
  <main>

    <!-- Q&A Section -->
    <div class="qa-section">
      <div class="qa-label">AI Research Assistant</div>
      <div class="qa-title">Ask a question about the Breakfast Leadership Show</div>
      <div class="qa-row">
        <input id="qa-input" type="text"
          placeholder="Show me all episodes about burnout from 2023"
          autocomplete="off">
        <button id="qa-btn" onclick="runQA()">Ask</button>
      </div>
      <div class="qa-examples">
        Try:
        <span onclick="fillQA('Show me all episodes about burnout from 2023')">burnout 2023</span> ·
        <span onclick="fillQA('Which episodes cover AI strategy with executive guests?')">AI strategy + executives</span> ·
        <span onclick="fillQA('Episodes about mental health and resilience')">mental health &amp; resilience</span> ·
        <span onclick="fillQA('Real estate investment episodes')">real estate</span>
      </div>
      <div class="loading" id="qa-loading"><div class="spinner"></div> Searching the knowledge base…</div>
      <div id="qa-results"></div>
    </div>

    <!-- Keyword Filter Bar -->
    <div class="filter-bar">
      <input id="search-input" type="text" placeholder="Filter by keyword — title, guest, description, or tag…" oninput="renderList()">
      <select class="sort-select" id="sort-select" onchange="renderList()">
        <option value="date-desc">Newest First</option>
        <option value="date-asc">Oldest First</option>
        <option value="alpha">A → Z</option>
      </select>
      <span class="result-count" id="result-count"></span>
    </div>

    <div id="episode-list"></div>

  </main>
</div>

<script>
// ── Data ────────────────────────────────────────────────────────────────────
const EPISODES = {episodes_json};

// ── State ───────────────────────────────────────────────────────────────────
let activeTag = null;

// ── Utilities ───────────────────────────────────────────────────────────────
const $ = id => document.getElementById(id);

function escHtml(s) {{
  return String(s ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}}

function formatDate(d) {{
  if (!d) return '';
  try {{ return new Date(d + 'T00:00:00').toLocaleDateString('en-US', {{year:'numeric',month:'short',day:'numeric'}}); }}
  catch {{ return d; }}
}}

// ── Build Sidebar ─────────────────────────────────────────────────────────
function buildSidebar() {{
  const counts = {{}};
  for (const ep of EPISODES) for (const t of (ep.tags||[])) counts[t] = (counts[t]||0) + 1;
  const tags = Object.entries(counts).sort((a,b) => b[1]-a[1]);
  const container = $('tag-list');
  let html = `<div class="tag-item all-tags ${{activeTag===null?'active':''}}" onclick="setTag(null)">
    <span>All Episodes</span><span class="count">${{EPISODES.length}}</span></div>`;
  for (const [tag, cnt] of tags) {{
    html += `<div class="tag-item ${{activeTag===tag?'active':''}}" onclick="setTag('${{escHtml(tag)}}')">
      <span>${{escHtml(tag)}}</span><span class="count">${{cnt}}</span></div>`;
  }}
  container.innerHTML = html;
  $('ep-total-header').textContent = '1,000+ episodes and growing';
}}

function setTag(tag) {{
  activeTag = tag;
  buildSidebar();
  renderList();
}}

// ── Episode List ──────────────────────────────────────────────────────────
function getFiltered() {{
  const q = $('search-input').value.trim().toLowerCase();
  let eps = EPISODES;
  if (activeTag) eps = eps.filter(ep => (ep.tags||[]).includes(activeTag));
  if (q) {{
    const terms = q.split(/\s+/);
    eps = eps.filter(ep => {{
      const hay = [ep.title, ep.guest, ep.description, ...(ep.tags||[])].join(' ').toLowerCase();
      return terms.every(t => hay.includes(t));
    }});
  }}
  return eps;
}}

function renderList() {{
  const sort = $('sort-select').value;
  let eps = getFiltered();
  if (sort === 'date-desc') eps = [...eps].sort((a,b) => (b.pub_date||'').localeCompare(a.pub_date||''));
  else if (sort === 'date-asc') eps = [...eps].sort((a,b) => (a.pub_date||'').localeCompare(b.pub_date||''));
  else eps = [...eps].sort((a,b) => (a.title||'').localeCompare(b.title||''));

  $('result-count').textContent = eps.length === EPISODES.length ? `1,000+ episodes and growing` : `${{eps.length}} of 1,000+ episodes`;

  if (!eps.length) {{
    $('episode-list').innerHTML = '<div class="no-results">No episodes match your search.</div>';
    return;
  }}

  $('episode-list').innerHTML = eps.map(ep => `
    <div class="ep-card">
      <div class="ep-header">
        ${{ep.episode_number ? `<span class="ep-num">#${{escHtml(ep.episode_number)}}</span>` : ''}}
        <div class="ep-title">
          <a href="${{escHtml(ep.episode_url)}}" target="_blank" rel="noopener">${{escHtml(ep.title)}}</a>
        </div>
      </div>
      <div class="ep-meta">
        ${{ep.guest ? `<span class="guest">👤 ${{escHtml(ep.guest)}}</span>` : ''}}
        ${{ep.pub_date ? `<span>${{formatDate(ep.pub_date)}}</span>` : ''}}
      </div>
      <div class="ep-tags">
        ${{(ep.tags||[]).map(t => `<span class="tag-pill" onclick="setTag('${{escHtml(t)}}')">${{escHtml(t)}}</span>`).join('')}}
      </div>
      ${{ep.description ? `<div class="ep-desc">${{escHtml(ep.description.slice(0,280))}}</div>` : ''}}
    </div>
  `).join('');
}}

// ── Q&A ───────────────────────────────────────────────────────────────────
function fillQA(text) {{
  $('qa-input').value = text;
  $('qa-input').focus();
}}

$('qa-input').addEventListener('keydown', e => {{ if (e.key === 'Enter') runQA(); }});

async function runQA() {{
  const query = $('qa-input').value.trim();
  if (!query) return;

  const proxyUrl = (typeof window.QA_PROXY_URL !== 'undefined') ? window.QA_PROXY_URL : '';
  if (!proxyUrl || proxyUrl === 'YOUR_WORKER_URL_HERE') {{
    $('qa-results').innerHTML = `<div class="qa-error">
      <strong>Proxy not configured.</strong> Add your Cloudflare Worker URL to <code>config.js</code> to enable the Q&amp;A feature.
      The keyword filter above still works without it.
    </div>`;
    return;
  }}

  const btn = $('qa-btn');
  btn.disabled = true;
  $('qa-loading').classList.add('show');
  $('qa-results').innerHTML = '';

  const systemPrompt = `You are a research assistant for the Breakfast Leadership Show podcast knowledge base. You have access to a dataset of over 1,000 episodes. When the user asks a question, return a JSON array of the most relevant episode_url values from the dataset (up to 15), ranked by relevance. For each match also include a "relevance" field: one sentence explaining why this episode fits the query. Return ONLY a JSON array of objects with shape: {{"episode_url": "...", "relevance": "..."}}, no preamble, no markdown fences.`;

  // Client-side pre-filter: score every episode, send top 100 to the API.
  // This keeps the payload well under 10K tokens on any query.
  const queryTerms = query.toLowerCase().split(/\s+/).filter(t => t.length > 2);
  const scored = EPISODES.map(ep => {{
    const hay = [ep.title, ep.guest, ...(ep.tags||[])].join(' ').toLowerCase();
    // Score: each matching term adds points; title matches worth more than tag matches
    let score = 0;
    for (const t of queryTerms) {{
      if ((ep.title||'').toLowerCase().includes(t)) score += 3;
      if ((ep.guest||'').toLowerCase().includes(t)) score += 2;
      if ((ep.tags||[]).join(' ').toLowerCase().includes(t)) score += 1;
    }}
    return {{ ep, score }};
  }});

  // Top 100: keyword matches ranked by score, padded with most-recent episodes
  const withHits = scored.filter(s => s.score > 0).sort((a,b) => b.score - a.score).map(s => s.ep);
  const recent   = scored.filter(s => s.score === 0).map(s => s.ep).slice(0, Math.max(0, 100 - withHits.length));
  const pool = [...withHits, ...recent].slice(0, 100);

  const compactIndex = pool.map(ep => ({{
    title: ep.title,
    guest: ep.guest || null,
    pub_date: ep.pub_date,
    tags: ep.tags || [],
    episode_url: ep.episode_url,
  }}));

  const userMessage = `Episode index (${{compactIndex.length}} most relevant episodes):
${{JSON.stringify(compactIndex)}}

User question: ${{query}}`;

  try {{
    const resp = await fetch(proxyUrl, {{
      method: 'POST',
      headers: {{ 'Content-Type': 'application/json' }},
      body: JSON.stringify({{
        model: 'claude-sonnet-5',
        max_tokens: 4096,
        system: systemPrompt,
        messages: [{{ role: 'user', content: userMessage }}],
      }}),
    }});

    if (!resp.ok) {{
      const err = await resp.json().catch(() => ({{}}));
      throw new Error(err.error?.message || `HTTP ${{resp.status}}`);
    }}

    const data = await resp.json();
    const text = data.content.filter(b => b.type === 'text').map(b => b.text).join('').trim();

    // Strip optional markdown fences
    const cleaned = text.replace(/^```(?:json)?\\s*/,'').replace(/\\s*```$/,'').trim();
    const aiResults = JSON.parse(cleaned);

    if (!Array.isArray(aiResults) || aiResults.length === 0) {{
      $('qa-results').innerHTML = '<div class="qa-error">No relevant episodes found for that query. Try rephrasing.</div>';
      return;
    }}

    // Build URL → episode lookup for instant local enrichment
    const byUrl = Object.fromEntries(EPISODES.map(e => [e.episode_url, e]));

    const cards = aiResults.slice(0, 15).flatMap((r, i) => {{
      const ep = byUrl[r.episode_url];
      // Skip results where the URL doesn't match a real episode (avoids "Untitled" / 404s)
      if (!ep || !ep.title) return [];
      const title = ep.title;
      const url   = ep.episode_url;
      const guest = ep.guest || null;
      const date  = ep.pub_date || '';
      const tags  = ep.tags || [];
      const why   = r.relevance || r.reason || '';
      return [`
      <div class="qa-result-card">
        <div class="ep-title">
          <span class="qa-rank">#${{i+1}}</span>
          <a href="${{escHtml(url)}}" target="_blank" rel="noopener">${{escHtml(title)}}</a>
        </div>
        <div class="qa-meta">
          ${{guest ? `👤 ${{escHtml(guest)}}  ·  ` : ''}}${{date ? formatDate(date) : ''}}
        </div>
        <div class="ep-tags">
          ${{tags.map(t => `<span class="tag-pill">${{escHtml(t)}}</span>`).join('')}}
        </div>
        ${{why ? `<div class="qa-relevance">${{escHtml(why)}}</div>` : ''}}
      </div>`];
    }});
    $('qa-results').innerHTML = cards.join('');

  }} catch (e) {{
    $('qa-results').innerHTML = `<div class="qa-error"><strong>Error:</strong> ${{escHtml(e.message)}}</div>`;
  }} finally {{
    btn.disabled = false;
    $('qa-loading').classList.remove('show');
  }}
}}

// ── Init ──────────────────────────────────────────────────────────────────
buildSidebar();
renderList();
</script>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)

print(f"Built index.html ({len(html):,} bytes, {len(episodes)} episodes embedded)")
