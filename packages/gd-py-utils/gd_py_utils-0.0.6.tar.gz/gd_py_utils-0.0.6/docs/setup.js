(function () {
  "use strict";

  // ---- Utils ---------------------------------------------------------------

  const onReady = (cb) => {
    if (typeof document$ !== "undefined" && document$?.subscribe) {
      document$.subscribe(({ body }) => cb(body));
    } else {
      document.addEventListener("DOMContentLoaded", () => cb(document));
    }
  };

  // ---- KaTeX auto-render ---------------------------------------------------

  const renderMath = (root) => {
    if (!window.renderMathInElement) return;

    renderMathInElement(root, {
      delimiters: [
        { left: "$$", right: "$$", display: true },
        { left: "$", right: "$", display: false },
        { left: "\\(", right: "\\)", display: false },
        { left: "\\[", right: "\\]", display: true },
      ],
      throwOnError: false,
    });
  };

  // ---- Mermaid init (once) -------------------------------------------------

  let mermaidInited = false;
  const initMermaidOnce = () => {
    if (mermaidInited) return;
    if (!window.mermaid?.initialize) return;

    // mkdocs-mermaid2-plugin usually drives rendering;
    // we only ensure mermaid is configured.
    mermaid.initialize({ startOnLoad: true });
    mermaidInited = true;
  };

  // ---- Mermaid popup modal + pan/zoom --------------------------------------

  let panZoom = null;

  const destroyPanZoom = () => {
    if (!panZoom) return;
    try {
      panZoom.destroy();
    } catch {
      // ignore
    }
    panZoom = null;
  };

  const ensureMermaidModal = () => {
    let modal = document.getElementById("mermaid-modal");
    if (modal) return modal;

    modal = document.createElement("div");
    modal.id = "mermaid-modal";
    modal.style.cssText = `
      position: fixed; inset: 0; z-index: 9999;
      display: none; align-items: center; justify-content: center;
      background: rgba(0,0,0,.55);
      padding: 24px;
    `;

    const panel = document.createElement("div");
    panel.id = "mermaid-modal-panel";
    panel.style.cssText = `
      position: relative;
      width: min(1200px, 96vw);
      height: min(800px, 92vh);
      background: var(--md-default-bg-color, #fff);
      border-radius: 12px;
      box-shadow: 0 10px 30px rgba(0,0,0,.35);
      overflow: hidden;
    `;

    const close = document.createElement("button");
    close.type = "button";
    close.textContent = "✕";
    close.setAttribute("aria-label", "Close");
    close.style.cssText = `
      position: absolute; top: 10px; right: 10px; z-index: 3;
      border: 0; border-radius: 10px;
      padding: 6px 10px; cursor: pointer;
      background: rgba(0,0,0,.08);
    `;

    const content = document.createElement("div");
    content.id = "mermaid-modal-content";
    content.style.cssText = `
      width: 100%; height: 100%;
      overflow: hidden;
      padding: 0;
    `;

    const hide = () => {
      destroyPanZoom();
      modal.style.display = "none";
      // Clean content to release references
      content.replaceChildren();
    };

    close.addEventListener("click", hide);
    modal.addEventListener("click", (e) => {
      if (e.target === modal) hide();
    });
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && modal.style.display !== "none") hide();
    });

    panel.appendChild(close);
    panel.appendChild(content);
    modal.appendChild(panel);
    document.body.appendChild(modal);
    return modal;
  };

  const openMermaidInModal = (svg) => {
    const modal = ensureMermaidModal();
    const content = document.getElementById("mermaid-modal-content");

    destroyPanZoom();

    // Wrap to allow svg-pan-zoom to size properly
    const wrap = document.createElement("div");
    wrap.style.cssText = `
      width: 100%;
      height: 100%;
      overflow: hidden;
      touch-action: none;
      background: var(--md-default-bg-color, #fff);
    `;

    const clone = svg.cloneNode(true);

    // Responsive sizing; pan/zoom handles viewBox transforms
    clone.removeAttribute("width");
    clone.removeAttribute("height");
    clone.style.width = "100%";
    clone.style.height = "100%";
    clone.style.display = "block";

    wrap.appendChild(clone);
    content.replaceChildren(wrap);

    modal.style.display = "flex";

    if (window.svgPanZoom) {
      // Needs to be in DOM + visible
      requestAnimationFrame(() => {
        panZoom = svgPanZoom(clone, {
          zoomEnabled: true,
          panEnabled: true,
          controlIconsEnabled: true,
          fit: true,
          center: true,
          minZoom: 0.1,
          maxZoom: 50,
          dblClickZoomEnabled: true,
          mouseWheelZoomEnabled: true,
          preventMouseEventsDefault: true,
        });
      });
    }
  };

  const attachMermaidPopupButtons = (root) => {
    const blocks = root.querySelectorAll(".mermaid");
    for (const block of blocks) {
      const svg = block.querySelector("svg");
      if (!svg) continue;

      if (block.dataset.popupAttached === "1") continue;
      block.dataset.popupAttached = "1";

      const btn = document.createElement("button");
      btn.type = "button";
      btn.textContent = "Open";
      btn.style.cssText = `
        margin: 6px 0 10px 0;
        padding: 4px 10px;
        border-radius: 10px;
        border: 1px solid rgba(0,0,0,.15);
        background: transparent;
        cursor: pointer;
        font: inherit;
      `;

      btn.addEventListener("click", () => openMermaidInModal(svg));

      block.parentElement?.insertBefore(btn, block);
    }
  };

  // ---- Main hook -----------------------------------------------------------

  onReady((body) => {
    initMermaidOnce();
    renderMath(body);

    // Mermaid rendering can be async; retry briefly to catch SVG insertion
    let tries = 0;
    const tick = () => {
      attachMermaidPopupButtons(body);
      if (++tries < 12) setTimeout(tick, 150);
    };
    tick();
  });
})();
