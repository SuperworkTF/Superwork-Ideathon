/* ============================================================
   SUPERWORK IDEATHON '26 — interaction layer (vanilla, no deps)
   Progressive enhancement: every page is fully readable without this file.
   reveal · scramble · glitch(css) · marquee · countdown · fair-shuffle
   · vote-CTA injection · custom cursor · reduced-motion aware
   ============================================================ */
(() => {
  "use strict";
  const D = (typeof window !== "undefined" && window.IDEATHON) || { meta: {}, ideas: [] };
  const meta = D.meta || {};
  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const finePointer = matchMedia("(pointer: fine)").matches;
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));

  document.documentElement.classList.add("js");

  /* ---- 1. Vote CTA href injection --------------------------- */
  $$("[data-vote-url]").forEach((a) => {
    if (meta.voteUrl && meta.voteUrl !== "#") {
      a.href = meta.voteUrl; a.target = "_blank"; a.rel = "noopener";
      a.removeAttribute("aria-disabled");
    } else {
      a.setAttribute("aria-disabled", "true");
      a.setAttribute("title", "투표 링크가 곧 연결됩니다");
    }
  });

  /* ---- 2. Countdown to deadline (text + segmented, tabular, flare) --- */
  const cds = $$("[data-countdown]");
  const seg = { d: $$("[data-cd-days]"), h: $$("[data-cd-hours]"), m: $$("[data-cd-mins]"), s: $$("[data-cd-secs]") };
  const wraps = $$("[data-cd-wrap]");
  if ((cds.length || seg.d.length) && meta.voteDeadline) {
    const end = new Date(meta.voteDeadline).getTime();
    const pad = (n) => String(n).padStart(2, "0");
    const setAll = (els, v) => els.forEach((e) => { e.textContent = v; });
    const render = () => {
      const diff = end - Date.now();
      if (isNaN(end)) return;
      if (diff <= 0) {
        cds.forEach((el) => { el.textContent = "투표 마감"; el.classList.add("is-closed"); });
        setAll(seg.d, "00"); setAll(seg.h, "00"); setAll(seg.m, "00"); setAll(seg.s, "00");
        wraps.forEach((w) => w.classList.add("is-closed"));
        return true;
      }
      const d = Math.floor(diff / 864e5);
      const h = Math.floor((diff % 864e5) / 36e5);
      const m = Math.floor((diff % 36e5) / 6e4);
      const s = Math.floor((diff % 6e4) / 1e3);
      cds.forEach((el) => { el.textContent = `D-${d} · ${pad(h)}:${pad(m)}:${pad(s)}`; });
      setAll(seg.d, pad(d)); setAll(seg.h, pad(h)); setAll(seg.m, pad(m)); setAll(seg.s, pad(s));
    };
    render();
    if (!reduce) { const iv = setInterval(() => { if (render() === true) clearInterval(iv); }, 1000); }
  }

  /* ---- 3. Scroll reveal (IntersectionObserver, all browsers) --- */
  const reveals = $$(".reveal");
  if (reveals.length && !reduce && "IntersectionObserver" in window) {
    reveals.forEach((el) => el.classList.add("js-hide"));
    const io = new IntersectionObserver((ents) => {
      ents.forEach((e) => { if (e.isIntersecting) { e.target.classList.add("is-in"); io.unobserve(e.target); } });
    }, { threshold: 0.14, rootMargin: "0px 0px -6% 0px" });
    reveals.forEach((el) => io.observe(el));
  }

  /* ---- 4. Text scramble / decode (hero, on first view) ------ */
  const GLYPHS = "!<>-_\\/[]{}—=+*^?#________";
  const rnd = () => GLYPHS[(Math.random() * GLYPHS.length) | 0];
  function scramble(el, dur) {
    const final = el.dataset.scrambleText || el.textContent;
    el.dataset.scrambleText = final;
    el.setAttribute("aria-label", final);
    if (reduce) { el.textContent = final; return; }
    const chars = final.split("");
    const start = performance.now();
    el.classList.add("is-scrambling");
    const frame = (now) => {
      const p = Math.min(1, (now - start) / (dur || 900));
      const settled = Math.floor(p * chars.length);
      let out = "";
      for (let i = 0; i < chars.length; i++) {
        const c = chars[i];
        out += (c === " " || c === "\n" || i < settled) ? c : rnd();
      }
      el.textContent = out;
      if (p < 1) requestAnimationFrame(frame);
      else { el.textContent = final; el.classList.remove("is-scrambling"); }
    };
    requestAnimationFrame(frame);
  }
  const scramblers = $$("[data-scramble]");
  if (scramblers.length) {
    if (reduce || !("IntersectionObserver" in window)) {
      scramblers.forEach((el) => { el.setAttribute("aria-label", el.textContent); });
    } else {
      const so = new IntersectionObserver((ents) => {
        ents.forEach((e) => { if (e.isIntersecting) { scramble(e.target, +e.target.dataset.scramble || 900); so.unobserve(e.target); } });
      }, { threshold: 0.55 });
      scramblers.forEach((el) => so.observe(el));
    }
  }

  /* ---- 5. Marquee: duplicate track for seamless loop -------- */
  $$(".marquee__track").forEach((tr) => {
    if (tr.dataset.dup === "1") return;
    tr.dataset.dup = "1";
    const clone = tr.innerHTML;
    tr.innerHTML = clone + clone;
    tr.setAttribute("aria-hidden", "false");
  });

  /* ---- 6. Fair-shuffle of finalist order (codes stay on cards) --- */
  $$("[data-shuffle]").forEach((box) => {
    const items = Array.from(box.children);
    for (let i = items.length - 1; i > 0; i--) {
      const j = (Math.random() * (i + 1)) | 0;
      if (j !== i) box.insertBefore(items[j], items[i].nextSibling);
      const t = items[i]; items[i] = items[j]; items[j] = t;
    }
    box.dataset.shuffled = "1";
  });

  /* ---- 7. Custom cursor (fine pointer, motion-ok) ----------- */
  if (finePointer && !reduce) {
    const dot = Object.assign(document.createElement("div"), { className: "cursor-dot" });
    const ring = Object.assign(document.createElement("div"), { className: "cursor-ring" });
    document.body.append(dot, ring);
    document.body.classList.add("cursor-active");
    let rx = 0, ry = 0, x = innerWidth / 2, y = innerHeight / 2;
    addEventListener("pointermove", (e) => {
      x = e.clientX; y = e.clientY;
      dot.style.transform = `translate(${x}px,${y}px) translate(-50%,-50%)`;
    }, { passive: true });
    (function loop() {
      rx += (x - rx) * 0.2; ry += (y - ry) * 0.2;
      ring.style.transform = `translate(${rx}px,${ry}px) translate(-50%,-50%)`;
      requestAnimationFrame(loop);
    })();
    const grow = () => { ring.style.width = "54px"; ring.style.height = "54px"; ring.style.background = "var(--accent)"; ring.style.borderColor = "var(--accent)"; };
    const shrink = () => { ring.style.width = "32px"; ring.style.height = "32px"; ring.style.background = "transparent"; ring.style.borderColor = "var(--chalk)"; };
    $$("a,button,[data-cursor]").forEach((el) => { el.addEventListener("pointerenter", grow); el.addEventListener("pointerleave", shrink); });
  }

  /* ---- 8. Small dynamic bits -------------------------------- */
  $$("[data-year]").forEach((el) => { el.textContent = new Date().getFullYear(); });
})();
