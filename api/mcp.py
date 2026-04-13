"""Vercel serverless entry point — MCP server + docs landing page."""

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.routing import Mount, Route

from src.server import mcp

DOCS_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Data Quality Agent — Retinal Image Quality Assessment</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  :root {
    --bg: #fafafa;
    --surface: #ffffff;
    --border: #e2e4e9;
    --border-light: #f0f1f3;
    --text: #1a1a2e;
    --text-secondary: #4a4a68;
    --muted: #6b7084;
    --accent: #c5050c;
    --accent-light: #e8383f;
    --accent-bg: #fef2f2;
    --blue: #2563eb;
    --blue-bg: #eff6ff;
    --green: #16a34a;
    --green-bg: #f0fdf4;
    --yellow: #ca8a04;
    --yellow-bg: #fefce8;
    --red: #dc2626;
    --red-bg: #fef2f2;
    --code-bg: #f4f5f7;
    --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
    --shadow-md: 0 4px 12px rgba(0,0,0,0.08);
    --radius: 0.625rem;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.65;
    -webkit-font-smoothing: antialiased;
  }

  /* --- Top bar --- */
  .topbar {
    background: var(--text);
    padding: 0.6rem 2rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  .topbar-left {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    color: #fff;
    font-size: 0.8rem;
    font-weight: 500;
    letter-spacing: 0.02em;
    text-transform: uppercase;
  }
  .topbar-left svg { opacity: 0.7; }
  .topbar a {
    color: rgba(255,255,255,0.7);
    text-decoration: none;
    font-size: 0.8rem;
    display: flex;
    align-items: center;
    gap: 0.4rem;
    transition: color 0.15s;
  }
  .topbar a:hover { color: #fff; }

  /* --- Hero --- */
  .hero {
    background: linear-gradient(135deg, var(--text) 0%, #2d2d4e 100%);
    padding: 3.5rem 2rem 3rem;
    text-align: center;
    position: relative;
    overflow: hidden;
  }
  .hero::before {
    content: '';
    position: absolute;
    top: -60%;
    left: -20%;
    width: 140%;
    height: 200%;
    background: radial-gradient(ellipse at center, rgba(197,5,12,0.08) 0%, transparent 70%);
    pointer-events: none;
  }
  .hero-eyeball {
    width: 72px;
    height: 72px;
    margin: 0 auto 1.25rem;
    opacity: 0.95;
  }
  .hero h1 {
    color: #fff;
    font-size: 2.2rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    margin-bottom: 0.5rem;
  }
  .hero p {
    color: rgba(255,255,255,0.65);
    font-size: 1.05rem;
    max-width: 540px;
    margin: 0 auto;
  }
  .hero-badges {
    display: flex;
    gap: 0.5rem;
    justify-content: center;
    margin-top: 1.25rem;
  }
  .badge {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    padding: 0.3rem 0.75rem;
    border-radius: 2rem;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.02em;
    text-transform: uppercase;
  }
  .badge-accent { background: var(--accent); color: #fff; }
  .badge-outline { background: rgba(255,255,255,0.1); color: rgba(255,255,255,0.8); border: 1px solid rgba(255,255,255,0.15); }

  /* --- Main content --- */
  .container { max-width: 880px; margin: 0 auto; padding: 0 1.5rem; }

  .section { padding: 2.5rem 0 0; }
  .section-label {
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--accent);
    margin-bottom: 0.4rem;
  }
  .section h2 {
    font-size: 1.4rem;
    font-weight: 700;
    color: var(--text);
    letter-spacing: -0.01em;
    margin-bottom: 0.5rem;
  }
  .section > p { color: var(--text-secondary); font-size: 0.95rem; }

  /* --- Endpoint card --- */
  .endpoint-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.25rem 1.5rem;
    margin-top: 1rem;
    box-shadow: var(--shadow-sm);
  }
  .endpoint-method {
    display: inline-block;
    background: var(--blue);
    color: #fff;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    font-weight: 600;
    padding: 0.2rem 0.55rem;
    border-radius: 0.25rem;
    margin-right: 0.5rem;
  }
  .endpoint-path {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.95rem;
    font-weight: 500;
    color: var(--text);
  }
  .endpoint-card p { color: var(--muted); font-size: 0.85rem; margin-top: 0.5rem; }
  .endpoint-card code {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem;
    background: var(--code-bg);
    padding: 0.1rem 0.35rem;
    border-radius: 0.2rem;
  }

  /* --- Tool cards --- */
  .tool-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.25rem 1.5rem;
    box-shadow: var(--shadow-sm);
    transition: box-shadow 0.15s, border-color 0.15s;
  }
  .tool-card:hover { box-shadow: var(--shadow-md); border-color: #d0d3d9; }
  .tool-card h3 {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--text);
    margin-bottom: 0.15rem;
  }
  .tool-card .tool-label {
    font-family: 'Inter', sans-serif;
    font-size: 0.75rem;
    font-weight: 500;
    color: var(--muted);
    margin-bottom: 0.4rem;
  }
  .tool-card p { color: var(--text-secondary); font-size: 0.88rem; }
  .tool-primary { border-left: 3px solid var(--accent); }
  .tool-dl { border-left: 3px solid var(--blue); }

  .tools-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.75rem;
    margin-top: 0.75rem;
  }
  @media (max-width: 640px) { .tools-grid { grid-template-columns: 1fr; } }

  /* --- Schema dropdowns --- */
  details { margin-top: 0.65rem; }
  summary {
    cursor: pointer;
    font-size: 0.78rem;
    font-weight: 500;
    color: var(--blue);
    user-select: none;
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
  }
  summary:hover { color: var(--accent); }
  summary::marker { content: ''; }
  summary::before {
    content: '\25B6';
    font-size: 0.55rem;
    transition: transform 0.15s;
    display: inline-block;
  }
  details[open] > summary::before { transform: rotate(90deg); }
  details pre {
    margin-top: 0.4rem;
    margin-bottom: 0;
    font-size: 0.78rem;
    background: var(--code-bg);
    color: var(--text);
    border: 1px solid var(--border-light);
    border-radius: 0.4rem;
    padding: 0.75rem 1rem;
    overflow-x: auto;
    line-height: 1.55;
  }
  details pre code {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    color: var(--text);
    background: none;
  }
  .schema-comment { color: var(--muted); }

  /* --- Verdict pills --- */
  .verdict { font-family: 'JetBrains Mono', monospace; font-weight: 700; font-size: 0.82rem; padding: 0.1rem 0.45rem; border-radius: 0.2rem; }
  .v-accept { background: var(--green-bg); color: var(--green); }
  .v-review { background: var(--yellow-bg); color: var(--yellow); }
  .v-reject { background: var(--red-bg); color: var(--red); }

  /* --- Code blocks --- */
  pre {
    background: var(--text);
    color: #e2e4e9;
    border-radius: var(--radius);
    padding: 1rem 1.25rem;
    overflow-x: auto;
    font-size: 0.82rem;
    line-height: 1.55;
    margin: 0.75rem 0;
  }
  pre code { font-family: 'JetBrains Mono', monospace; font-size: 0.82rem; color: inherit; background: none; }
  .inline-code {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.82rem;
    background: var(--code-bg);
    padding: 0.15rem 0.4rem;
    border-radius: 0.25rem;
  }

  /* --- Tables --- */
  table { width: 100%; border-collapse: collapse; margin: 0.75rem 0; }
  th { text-align: left; padding: 0.6rem 0.75rem; font-size: 0.78rem; font-weight: 600; color: var(--muted); text-transform: uppercase; letter-spacing: 0.04em; border-bottom: 2px solid var(--border); }
  td { padding: 0.55rem 0.75rem; border-bottom: 1px solid var(--border-light); font-size: 0.88rem; color: var(--text-secondary); }
  td:first-child { font-family: 'JetBrains Mono', monospace; font-size: 0.82rem; color: var(--text); white-space: nowrap; }

  /* --- Footer --- */
  .footer {
    margin-top: 3rem;
    padding: 1.5rem 0;
    border-top: 1px solid var(--border);
    text-align: center;
  }
  .footer p { color: var(--muted); font-size: 0.8rem; }
  .footer a { color: var(--accent); }

  /* --- Misc --- */
  h3.subsection { font-size: 0.95rem; font-weight: 600; margin: 1.25rem 0 0.4rem; color: var(--text); }
  .note { color: var(--muted); font-size: 0.82rem; margin-top: 0.5rem; }
</style>
</head>
<body>

<!-- Top bar -->
<div class="topbar">
  <div class="topbar-left">
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></svg>
    Built for the Wisconsin Reading Center
  </div>
  <a href="https://github.com/tejvirmann/data-quality-agent" target="_blank" rel="noopener">
    <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/></svg>
    GitHub
  </a>
</div>

<!-- Hero -->
<div class="hero">
  <!-- Eyeball SVG -->
  <svg class="hero-eyeball" viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg">
    <!-- Outer eye shape -->
    <ellipse cx="60" cy="60" rx="54" ry="36" fill="#1a1a2e" stroke="rgba(255,255,255,0.15)" stroke-width="1"/>
    <!-- Sclera -->
    <ellipse cx="60" cy="60" rx="48" ry="32" fill="#f0f0f0"/>
    <!-- Iris outer -->
    <circle cx="60" cy="60" r="22" fill="#8B4513"/>
    <!-- Iris detail rings -->
    <circle cx="60" cy="60" r="22" fill="url(#iris-grad)"/>
    <circle cx="60" cy="60" r="18" stroke="rgba(0,0,0,0.1)" stroke-width="0.5" fill="none"/>
    <circle cx="60" cy="60" r="15" stroke="rgba(0,0,0,0.08)" stroke-width="0.5" fill="none"/>
    <!-- Iris radial lines -->
    <g stroke="rgba(60,30,0,0.2)" stroke-width="0.4">
      <line x1="60" y1="38" x2="60" y2="50"/><line x1="60" y1="70" x2="60" y2="82"/>
      <line x1="38" y1="60" x2="50" y2="60"/><line x1="70" y1="60" x2="82" y2="60"/>
      <line x1="44.4" y1="44.4" x2="52" y2="52"/><line x1="68" y1="68" x2="75.6" y2="75.6"/>
      <line x1="75.6" y1="44.4" x2="68" y2="52"/><line x1="52" y1="68" x2="44.4" y2="75.6"/>
    </g>
    <!-- Pupil -->
    <circle cx="60" cy="60" r="10" fill="#0a0a0a"/>
    <!-- Light reflection -->
    <ellipse cx="53" cy="53" rx="4" ry="3" fill="rgba(255,255,255,0.85)" transform="rotate(-20 53 53)"/>
    <circle cx="67" cy="66" r="1.5" fill="rgba(255,255,255,0.4)"/>
    <!-- Retinal vessels hint (visible through pupil) -->
    <g stroke="#8B0000" stroke-width="0.6" opacity="0.25">
      <path d="M54 60 Q50 55 45 53"/>
      <path d="M54 60 Q50 65 44 68"/>
      <path d="M66 60 Q70 55 76 54"/>
      <path d="M66 60 Q70 65 75 67"/>
    </g>
    <!-- Scan line animation -->
    <line x1="12" y1="60" x2="108" y2="60" stroke="var(--accent)" stroke-width="0.5" opacity="0.3">
      <animate attributeName="y1" values="40;80;40" dur="3s" repeatCount="indefinite"/>
      <animate attributeName="y2" values="40;80;40" dur="3s" repeatCount="indefinite"/>
    </line>
    <defs>
      <radialGradient id="iris-grad" cx="0.45" cy="0.45">
        <stop offset="0%" stop-color="#A0652A"/>
        <stop offset="50%" stop-color="#7B4B1E"/>
        <stop offset="100%" stop-color="#5C3310"/>
      </radialGradient>
    </defs>
  </svg>

  <h1>Data Quality Agent</h1>
  <p>Automated retinal image quality assessment for the Wisconsin Reading Center. MCP server with classical computer vision and deep learning checks.</p>
  <div class="hero-badges">
    <span class="badge badge-accent">MCP Protocol</span>
    <span class="badge badge-outline">Streamable HTTP</span>
    <span class="badge badge-outline">8 Quality Tools</span>
  </div>
</div>

<div class="container">

  <!-- What is this -->
  <div class="section">
    <div class="section-label">Overview</div>
    <h2>What is this?</h2>
    <p>A <strong>Model Context Protocol (MCP)</strong> server that accepts retinal fundus image URLs and evaluates
    them for diagnostic quality. It runs 7 classical computer vision checks plus an optional deep learning model
    (EyeQ/MCF-Net) and returns an
    <span class="verdict v-accept">ACCEPT</span>,
    <span class="verdict v-review">REVIEW</span>, or
    <span class="verdict v-reject">REJECT</span> verdict.</p>
    <p style="margin-top:0.5rem">Connect this server to <a href="https://opencode.ai">OpenCode</a>,
    Claude Desktop, or any MCP-compatible assistant to quality-gate images before human grading.</p>
  </div>

  <!-- Endpoint -->
  <div class="section">
    <div class="section-label">Endpoint</div>
    <h2>MCP Endpoint</h2>
    <div class="endpoint-card">
      <div>
        <span class="endpoint-method">POST</span>
        <span class="endpoint-path">/mcp</span>
      </div>
      <p>Streamable HTTP transport. JSON-RPC 2.0 with headers
      <code>Content-Type: application/json</code> and
      <code>Accept: application/json, text/event-stream</code></p>
    </div>
  </div>

  <!-- Tools -->
  <div class="section">
    <div class="section-label">API Reference</div>
    <h2>Tools</h2>

    <!-- Orchestrator -->
    <div class="tool-card tool-primary" style="margin-top:0.75rem">
      <h3>tool_check_image_quality</h3>
      <div class="tool-label">Full Quality Report &mdash; Primary Tool</div>
      <p>Runs ALL checks and returns a combined verdict with individual results. Use this for a single comprehensive assessment.</p>
      <details>
        <summary>Input Parameters</summary>
        <pre><code>{
  "image_url": {
    "type": "string",
    "format": "uri",
    "required": true,
    "description": "Publicly accessible URL of the image to check"
  }
}</code></pre>
      </details>
      <details>
        <summary>Output Schema &mdash; QualityReport</summary>
        <pre><code>{
  "verdict": "accept" | "review" | "reject",
  "checks": [
    {
      "name": "string",        <span class="schema-comment">// e.g. "sharpness", "resolution"</span>
      "passed": true | false,
      "detail": "string"       <span class="schema-comment">// human-readable explanation</span>
    }
  ],
  "fundus_assessment": {       <span class="schema-comment">// null if EyeQ unavailable</span>
    "grade": "good" | "usable" | "reject",
    "confidence": 0.95,
    "probabilities": {
      "good": 0.95, "usable": 0.04, "reject": 0.01
    }
  },
  "image_url": "string"
}</code></pre>
      </details>
    </div>

    <div class="tools-grid">

      <div class="tool-card">
        <h3>tool_check_sharpness</h3>
        <div class="tool-label">Blur Detection</div>
        <p>Laplacian variance analysis. Score &gt;150 = sharp, &lt;80 = blurry.</p>
        <details>
          <summary>Input Parameters</summary>
          <pre><code>{
  "image_url": {
    "type": "string", "format": "uri",
    "required": true,
    "description": "Public image URL"
  }
}</code></pre>
        </details>
        <details>
          <summary>Output &mdash; SharpnessResult</summary>
          <pre><code>{
  "score": 155.3,       <span class="schema-comment">// Laplacian variance</span>
  "is_sharp": true,     <span class="schema-comment">// pass/fail</span>
  "detail": "string"
}</code></pre>
        </details>
      </div>

      <div class="tool-card">
        <h3>tool_check_resolution</h3>
        <div class="tool-label">Dimension Validation</div>
        <p>Checks width/height against minimums (default 1024&times;1024).</p>
        <details>
          <summary>Input Parameters</summary>
          <pre><code>{
  "image_url": {
    "type": "string", "format": "uri",
    "required": true,
    "description": "Public image URL"
  }
}</code></pre>
        </details>
        <details>
          <summary>Output &mdash; ResolutionResult</summary>
          <pre><code>{
  "width": 2048,
  "height": 2048,
  "meets_minimum": true,
  "megapixels": 4.19
}</code></pre>
        </details>
      </div>

      <div class="tool-card">
        <h3>tool_check_format</h3>
        <div class="tool-label">Format &amp; Corruption</div>
        <p>Validates file type via magic bytes. Detects truncated or corrupted files.</p>
        <details>
          <summary>Input Parameters</summary>
          <pre><code>{
  "image_url": {
    "type": "string", "format": "uri",
    "required": true,
    "description": "Public image URL"
  }
}</code></pre>
        </details>
        <details>
          <summary>Output &mdash; FormatResult</summary>
          <pre><code>{
  "format": "JPEG",
  "valid": true,
  "corrupted": false,
  "detail": "string"
}</code></pre>
        </details>
      </div>

      <div class="tool-card">
        <h3>tool_check_illumination</h3>
        <div class="tool-label">Exposure &amp; Vignetting</div>
        <p>Brightness uniformity, over/underexposure, and dark-corner detection.</p>
        <details>
          <summary>Input Parameters</summary>
          <pre><code>{
  "image_url": {
    "type": "string", "format": "uri",
    "required": true,
    "description": "Public image URL"
  }
}</code></pre>
        </details>
        <details>
          <summary>Output &mdash; IlluminationResult</summary>
          <pre><code>{
  "mean_brightness": 128.5,
  "std_brightness": 42.3,
  "uniform": true,
  "vignetting_detected": false,
  "detail": "string"
}</code></pre>
        </details>
      </div>

      <div class="tool-card">
        <h3>tool_check_color</h3>
        <div class="tool-label">Color Balance</div>
        <p>RGB validation and channel imbalance detection (tint, wash-out).</p>
        <details>
          <summary>Input Parameters</summary>
          <pre><code>{
  "image_url": {
    "type": "string", "format": "uri",
    "required": true,
    "description": "Public image URL"
  }
}</code></pre>
        </details>
        <details>
          <summary>Output &mdash; ColorResult</summary>
          <pre><code>{
  "mode": "RGB",
  "channels": 3,
  "balanced": true,
  "channel_means": [130.2, 125.8, 122.1],
  "detail": "string"
}</code></pre>
        </details>
      </div>

      <div class="tool-card">
        <h3>tool_validate_metadata</h3>
        <div class="tool-label">EXIF Extraction</div>
        <p>Extracts camera model, capture date, dimensions, and other metadata.</p>
        <details>
          <summary>Input Parameters</summary>
          <pre><code>{
  "image_url": {
    "type": "string", "format": "uri",
    "required": true,
    "description": "Public image URL"
  }
}</code></pre>
        </details>
        <details>
          <summary>Output &mdash; MetadataResult</summary>
          <pre><code>{
  "has_exif": true,
  "fields": {
    "Make": "Canon",
    "Model": "EOS R5",
    "DateTime": "2026:03:15 14:30:00"
  }
}</code></pre>
        </details>
      </div>

    </div>

    <!-- EyeQ -->
    <div class="tool-card tool-dl" style="margin-top:0.75rem">
      <h3>tool_assess_fundus_quality</h3>
      <div class="tool-label">Deep Learning &mdash; EyeQ / MCF-Net</div>
      <p>DenseNet121-based multi-color-space fusion model trained on fundus images. Processes in RGB, HSV, and LAB and returns
      <strong>Good</strong> / <strong>Usable</strong> / <strong>Reject</strong> with confidence scores.</p>
      <details>
        <summary>Input Parameters</summary>
        <pre><code>{
  "image_url": {
    "type": "string", "format": "uri",
    "required": true,
    "description": "Public URL of a fundus/retinal image"
  }
}</code></pre>
      </details>
      <details>
        <summary>Output &mdash; FundusAssessment</summary>
        <pre><code>{
  "grade": "good" | "usable" | "reject",
  "confidence": 0.95,
  "probabilities": {
    "good": 0.95,
    "usable": 0.04,
    "reject": 0.01
  }
}</code></pre>
      </details>
    </div>

    <p class="note">All tools accept a single parameter: <code class="inline-code">image_url</code> (string) &mdash; a publicly accessible image URL.</p>
  </div>

  <!-- Connect -->
  <div class="section">
    <div class="section-label">Integration</div>
    <h2>Connect Your Agent</h2>

    <h3 class="subsection">OpenCode</h3>
    <pre><code>{
  "mcp": {
    "data-quality": {
      "type": "remote",
      "url": "https://YOUR_DEPLOYMENT_URL/mcp",
      "enabled": true
    }
  }
}</code></pre>

    <h3 class="subsection">Claude Desktop</h3>
    <pre><code>{
  "mcpServers": {
    "data-quality": {
      "url": "https://YOUR_DEPLOYMENT_URL/mcp"
    }
  }
}</code></pre>
  </div>

  <!-- Curl -->
  <div class="section">
    <div class="section-label">Testing</div>
    <h2>Test with curl</h2>

    <h3 class="subsection">1. Initialize session</h3>
    <pre><code>curl -X POST /mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{
    "protocolVersion":"2025-03-26","capabilities":{},
    "clientInfo":{"name":"test","version":"0.1"}}}' \
  -i</code></pre>
    <p class="note">Copy the <code class="inline-code">Mcp-Session-Id</code> header from the response.</p>

    <h3 class="subsection">2. List tools</h3>
    <pre><code>curl -X POST /mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Mcp-Session-Id: YOUR_SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'</code></pre>

    <h3 class="subsection">3. Run full quality check</h3>
    <pre><code>curl -X POST /mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Mcp-Session-Id: YOUR_SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{
    "name":"tool_check_image_quality",
    "arguments":{"image_url":"https://picsum.photos/2048/2048.jpg"}}}'</code></pre>
  </div>

  <!-- Config -->
  <div class="section">
    <div class="section-label">Settings</div>
    <h2>Configuration</h2>
    <p>All thresholds are configurable via environment variables:</p>
    <table>
      <tr><th>Variable</th><th>Default</th><th>Description</th></tr>
      <tr><td>QUALITY_SHARPNESS_PASS</td><td>150</td><td>Sharpness score to pass</td></tr>
      <tr><td>QUALITY_SHARPNESS_REVIEW</td><td>80</td><td>Sharpness score for review</td></tr>
      <tr><td>QUALITY_MIN_WIDTH</td><td>1024</td><td>Minimum image width (px)</td></tr>
      <tr><td>QUALITY_MIN_HEIGHT</td><td>1024</td><td>Minimum image height (px)</td></tr>
      <tr><td>QUALITY_BRIGHTNESS_MIN_PASS</td><td>60</td><td>Min brightness to pass</td></tr>
      <tr><td>QUALITY_BRIGHTNESS_MAX_PASS</td><td>200</td><td>Max brightness to pass</td></tr>
      <tr><td>QUALITY_COLOR_BALANCE_PASS</td><td>30</td><td>Max channel diff to pass</td></tr>
      <tr><td>QUALITY_ALLOWED_FORMATS</td><td>JPEG,PNG,TIFF,BMP</td><td>Accepted file formats</td></tr>
      <tr><td>QUALITY_EYEQ_ENABLED</td><td>true</td><td>Enable EyeQ deep learning</td></tr>
    </table>
  </div>

  <!-- Tech -->
  <div class="section">
    <div class="section-label">Built with</div>
    <h2>Tech Stack</h2>
    <p>Python &middot; Pydantic &middot; FastMCP &middot; OpenCV &middot; Pillow &middot; PyTorch + EyeQ/MCF-Net &middot; Vercel</p>
  </div>

  <div class="footer">
    <p>Data Quality Agent &mdash; Built for the <a href="https://www.ophth.wisc.edu/research/wrc/">Wisconsin Reading Center</a></p>
  </div>

</div>
</body>
</html>
"""


async def docs_page(request: Request) -> HTMLResponse:
    return HTMLResponse(DOCS_HTML)


mcp_app = mcp.streamable_http_app()

app = Starlette(
    routes=[
        Route("/", docs_page),
        Mount("/mcp", app=mcp_app),
    ],
)
