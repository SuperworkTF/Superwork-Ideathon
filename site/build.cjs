#!/usr/bin/env node
/* Static generator — reads assets/config.js (single source of truth),
   writes ideas/<slug>.html for each finalist. No score/author/rank emitted.
   Run:  node site/build.cjs   (idempotent) */
const fs = require("fs");
const path = require("path");
const D = require(path.join(__dirname, "assets", "config.js"));
const { meta, ideas } = D;
const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

const FONTS = `
<link rel="preconnect" href="https://cdn.jsdelivr.net" crossorigin>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/wanteddev/wanted-sans@v1.0.3/packages/wanted-sans/fonts/webfonts/variable/split/WantedSansVariable.min.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Space+Mono:ital,wght@0,400;0,700;1,400;1,700&display=swap">`;

function featCell(f, i) {
  return `
        <div class="feat reveal">
          <div class="feat__k">${esc(f.label)}</div>
          <h3 class="feat__t">${esc(f.title)}</h3>
          <p class="feat__b">${esc(f.body)}</p>
          <div class="feat__i" aria-hidden="true">0${i + 1}</div>
        </div>`;
}

function page(idea, prev, next) {
  const tags = idea.tags.map((t) => `<span class="tag tag--accent">${esc(t)}</span>`).join("\n          ");
  return `<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>${esc(idea.name)} — ${esc(idea.tagline)} | IDEATHON ’26 결선</title>
<meta name="description" content="${esc(idea.hook)}">
<meta name="color-scheme" content="dark">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' fill='%230B0B0C'/%3E%3Crect x='6' y='6' width='20' height='20' fill='${encodeURIComponent(idea.accent)}'/%3E%3C/svg%3E">
<meta property="og:title" content="${esc(idea.name)} — ${idea.mono}">
<meta property="og:description" content="${esc(idea.tagline)}">
${FONTS}
<link rel="stylesheet" href="../assets/app.css">
</head>
<body style="--accent:${idea.accent};--accent-ink:${idea.accentInk}">
<div class="grain" aria-hidden="true"></div>

<header class="topbar">
  <a class="topbar__brand" href="../index.html">SUPERWORK<span class="acid">/</span>IDEATHON ’26</a>
  <div class="topbar__mid" aria-hidden="true">
    <span class="label" style="color:var(--smoke)">투표 마감</span>
    <span class="cd tnum" data-countdown>D-—</span>
  </div>
  <a class="btn" data-vote-url href="#" data-cursor>투표하러 가기 <span class="ar">→</span></a>
</header>

<main class="wrap">

  <nav class="crumb"><a href="../index.html">INDEX</a><span>/</span><span class="accent">${idea.mono}</span></nav>

  <!-- HERO -->
  <section class="dhero">
    <div class="dhero__num" aria-hidden="true" style="view-transition-name:n-${idea.slug}">${idea.mono}</div>
    <div class="dhero__body">
      <div class="dhero__tags">
          ${tags}
      </div>
      <h1 class="dhero__title" data-scramble="1100">${esc(idea.name)}</h1>
      <div class="dhero__en">${esc(idea.en)}</div>
      <p class="dhero__hook">${esc(idea.hook)}</p>
    </div>
  </section>

  <!-- 01 PROBLEM -->
  <section class="sect reveal">
    <div><div class="sect__no">01</div><div class="sect__label label">문제 · PROBLEM</div></div>
    <p class="sect__body">${esc(idea.problem)}</p>
  </section>

  <!-- 02 TARGET -->
  <section class="sect reveal">
    <div><div class="sect__no">02</div><div class="sect__label label">타깃 · TARGET</div></div>
    <p class="sect__body">${esc(idea.target)}</p>
  </section>

  <!-- 03 FEATURES -->
  <section class="sect">
    <div><div class="sect__no">03</div><div class="sect__label label">핵심기능 · FEATURES</div></div>
    <div class="feat2">${idea.features.map(featCell).join("")}
    </div>
  </section>

  <!-- 04 IMPACT -->
  <section class="sect reveal">
    <div><div class="sect__no">04</div><div class="sect__label label">임팩트 · IMPACT</div></div>
    <p class="sect__body">${esc(idea.impact)}</p>
  </section>

  <!-- CTA -->
  <section class="section--tight">
    <div class="dcta reveal">
      <div>
        <p class="dcta__lead">이 아이디어가 좋다면,<br>한 표.</p>
        <p class="dcta__meta">투표 마감 · 2026.07.03 (금) 18:00 KST<br>EXTERNAL · 전사 투표 채널</p>
      </div>
      <a class="btn" data-vote-url href="#" data-cursor>투표하러 가기 <span class="ar">→</span></a>
    </div>
  </section>

  <!-- PREV / NEXT -->
  <nav class="prevnext" aria-label="다른 결선작">
    <a class="pn pn--prev" href="${prev.slug}.html" data-cursor>
      <span class="pn__k">← PREV</span>
      <span class="pn__t">${esc(prev.name)}</span>
    </a>
    <a class="pn pn--next" href="${next.slug}.html" data-cursor>
      <span class="pn__k">NEXT →</span>
      <span class="pn__t">${esc(next.name)}</span>
    </a>
  </nav>

  <footer class="foot">
    <a href="../index.html" data-cursor>← 전체 결선작 보기</a>
    <span>ANONYMOUS SHOWCASE · <span data-year>2026</span></span>
  </footer>

</main>

<script src="../assets/config.js"></script>
<script src="../assets/app.js"></script>
</body>
</html>
`;
}

const outDir = path.join(__dirname, "ideas");
fs.mkdirSync(outDir, { recursive: true });
ideas.forEach((idea, i) => {
  const prev = ideas[(i - 1 + ideas.length) % ideas.length];
  const next = ideas[(i + 1) % ideas.length];
  const file = path.join(outDir, idea.slug + ".html");
  fs.writeFileSync(file, page(idea, prev, next));
  console.log("wrote", path.relative(__dirname, file));
});
console.log(`done — ${ideas.length} detail pages`);
