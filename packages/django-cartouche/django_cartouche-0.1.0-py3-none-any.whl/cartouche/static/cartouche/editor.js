(function () {
  "use strict";

  const dataEl = document.getElementById("cartouche-data");
  if (!dataEl) return;

  const data = JSON.parse(dataEl.textContent);
  const entries = new Map(
    data.t
      .sort((a, b) => b.msgstr.length - a.msgstr.length)
      .map((e) => [e.msgstr, e])
  );

  const SKIP = new Set([
    "SCRIPT",
    "STYLE",
    "TEXTAREA",
    "INPUT",
    "NOSCRIPT",
    "IFRAME",
  ]);

  function walk(node) {
    if (node.nodeType === Node.TEXT_NODE) {
      processText(node);
    } else if (node.nodeType === Node.ELEMENT_NODE && !SKIP.has(node.tagName)) {
      for (const child of Array.from(node.childNodes)) walk(child);
    }
  }

  function processText(node) {
    const text = node.textContent;
    for (const [msgstr, entry] of entries) {
      const idx = text.indexOf(msgstr);
      if (idx === -1) continue;

      const before = text.slice(0, idx);
      const after = text.slice(idx + msgstr.length);

      const span = document.createElement("span");
      span.className = "cartouche";
      span.contentEditable = "true";
      span.textContent = msgstr;
      span.dataset.msgid = entry.msgid;
      span.dataset.ctx = entry.ctx || "";
      span.dataset.orig = msgstr;
      span.addEventListener("blur", onBlur);
      span.addEventListener("keydown", onKey);

      const frag = document.createDocumentFragment();
      if (before) frag.appendChild(document.createTextNode(before));
      frag.appendChild(span);
      if (after) frag.appendChild(document.createTextNode(after));
      node.replaceWith(frag);
      return;
    }
  }

  function onKey(e) {
    if (e.key === "Escape") {
      e.target.textContent = e.target.dataset.orig;
      e.target.blur();
    } else if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      e.target.blur();
    }
  }

  async function onBlur(e) {
    const el = e.target;
    const newVal = el.textContent.trim();
    if (newVal === el.dataset.orig) return;

    el.classList.add("cartouche--saving");
    try {
      const res = await fetch("/cartouche/save/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": data.csrf,
        },
        body: JSON.stringify({
          msgid: el.dataset.msgid,
          msgstr: newVal,
          locale: document.documentElement.lang || "es",
          ctx: el.dataset.ctx || null,
        }),
      });
      const result = await res.json();
      el.classList.toggle("cartouche--ok", result.ok);
      el.classList.toggle("cartouche--err", !result.ok);
      if (result.ok) el.dataset.orig = newVal;
    } catch {
      el.classList.add("cartouche--err");
    } finally {
      el.classList.remove("cartouche--saving");
      setTimeout(
        () => el.classList.remove("cartouche--ok", "cartouche--err"),
        600
      );
    }
  }

  walk(document.body);
})();
