/* ============================================================
   preservation.studio — Vibe Tuner (?vibe=1 only)
   Live palette + type tuning, persisted per-browser (localStorage).
   Export the resulting :root block to lock a vibe into site.css.
   ============================================================ */
(function () {
  "use strict";

  var KEY = "ps-vibe-v1";

  var TOKENS = [
    ["paper", "Paper"],
    ["paper-deep", "Paper deep"],
    ["card", "Card"],
    ["ink", "Ink"],
    ["ink-soft", "Ink soft"],
    ["ink-faint", "Ink faint"],
    ["rule", "Rule"],
    ["rule-strong", "Rule strong"],
    ["butter", "Honey"],
    ["butter-soft", "Honey soft"],
    ["on-butter", "On honey"],
    ["blue", "Blue"],
    ["blue-soft", "Blue soft"],
    ["plum", "Plum"],
    ["on-plum", "On plum"],
    ["error", "Error"],
  ];

  var STACKS = {
    display: {
      fraunces: '"Fraunces", Georgia, serif',
      playfair: '"Playfair Display", Georgia, serif',
      cormorant: '"Cormorant Garamond", Georgia, serif',
      gloock: '"Gloock", Georgia, serif',
      italiana: '"Italiana", Georgia, serif',
      librebodoni: '"Libre Bodoni", "Playfair Display", Georgia, serif',
      bricolage: '"Bricolage Grotesque", "Space Grotesk", sans-serif',
      georgia: "Georgia, serif",
    },
    body: {
      newsreader: '"Newsreader", Georgia, "Times New Roman", serif',
      librecaslon: '"Libre Caslon Text", "Times New Roman", serif',
      sourceserif: '"Source Serif 4", Georgia, serif',
      cormorant: '"Cormorant Garamond", Georgia, serif',
      inter: '"Inter", "Helvetica Neue", Arial, sans-serif',
      switzer: '"Switzer", "Inter", "Helvetica Neue", Arial, sans-serif',
      spacegrotesk: '"Space Grotesk", "Helvetica Neue", sans-serif',
      archivo: '"Archivo", "Helvetica Neue", Arial, sans-serif',
      fraunces: '"Fraunces", Georgia, serif',
      georgia: "Georgia, serif",
    },
    mono: {
      plex: '"IBM Plex Mono", "Courier New", monospace',
      jetbrains: '"JetBrains Mono", "Courier New", monospace',
      spacemono: '"Space Mono", "Courier New", monospace',
      courier: '"Courier New", monospace',
    },
    hand: {
      kalam: '"Kalam", "Caveat", cursive',
      caveat: '"Caveat", cursive',
      dancingscript: '"Dancing Script", "Caveat", cursive',
      pacifico: '"Pacifico", cursive',
      satisfy: '"Satisfy", cursive',
      yellowtail: '"Yellowtail", cursive',
      grandhotel: '"Grand Hotel", cursive',
      kaushanscript: '"Kaushan Script", "Yellowtail", cursive',
      permanentmarker: '"Permanent Marker", "Kaushan Script", cursive',
    },
  };

  var STACK_VARS = {
    display: "--display",
    body: "--serif",
    mono: "--mono",
    hand: "--hand",
  };

  var SLIDERS = [
    ["fx-wonk", "WONK (wonkiness)", 0, 100, 1, "num100"],
    ["fx-soft", "SOFT (roundness)", 0, 100, 1, "num"],
    ["fx-opsz", "Optical size", 9, 144, 1, "num"],
    ["fx-wght", "Display weight", 100, 900, 1, "num"],
    ["hand-size", "Note size", 0.8, 1.6, 0.05, "rem"],
    ["hand-rotate", "Note tilt", -5, 5, 0.1, "deg"],
  ];

  /* ---------- Looks ----------
     Full recreations of what the client actually linked, as one-click
     states. Each preset is complete (palette + four stacks + dials) so
     applying one never leaves a stray value from the look before it.
     Every `note` records where the look came from. */

  var PLEX = '"IBM Plex Mono", "Courier New", ui-monospace, monospace';
  var SANS = '"Newsreader", Georgia, "Times New Roman", serif';

  var PRESETS = [
    {
      id: "bold-red",
      label: "Bold Red — template",
      note: 'Ships as the site default. From the "Bold Red" Squarespace template Asher linked (RowMarketCo, Etsy): cream paper, brick-red accent, maroon bands.',
      tokens: {
        paper: "#f2ecdf",
        "paper-deep": "#e7dfd0",
        card: "#fbf6ec",
        ink: "#201915",
        "ink-soft": "#5c5248",
        "ink-faint": "#978b7c",
        rule: "#ddd3c1",
        "rule-strong": "#c0b29b",
        butter: "#a63a2e",
        "butter-soft": "#f2dbd4",
        "on-butter": "#fdf8ef",
        blue: "#3f5a44",
        "blue-soft": "#dde4db",
        plum: "#8a332f",
        "on-plum": "#f5eee1",
        error: "#a6402e",
      },
      stacks: {
        "--display": '"Fraunces", Georgia, serif',
        "--serif": SANS,
        "--mono": PLEX,
        "--hand": '"Kalam", "Caveat", cursive',
      },
      sliders: {
        "--fx-opsz": "110",
        "--fx-wght": "560",
        "--fx-soft": "60",
        "--fx-wonk": "0.60",
        "--hand-size": "1.15rem",
        "--hand-rotate": "-1.6deg",
      },
    },
    {
      id: "canva-mockup",
      label: "Asher's Canva mockup",
      note: "Palette read straight off Asher's Canva design: cream #F5F1EA field, brick red #842B2C, light-orange #EEDBBC bands, greige #D1C8B7 rules, navy #182C59 secondary. Flatter, bolder blocking than the template.",
      tokens: {
        paper: "#f5f1ea",
        "paper-deep": "#eedbbc",
        card: "#ffffff",
        ink: "#17130f",
        "ink-soft": "#5f5a52",
        "ink-faint": "#9a938a",
        rule: "#e4dcce",
        "rule-strong": "#d1c8b7",
        butter: "#842b2c",
        "butter-soft": "#f0dcd5",
        "on-butter": "#fdf8ef",
        blue: "#182c59",
        "blue-soft": "#dce3f0",
        plum: "#6e2324",
        "on-plum": "#f5f1ea",
        error: "#a6402e",
      },
      stacks: {
        "--display": '"Fraunces", Georgia, serif',
        "--serif": SANS,
        "--mono": PLEX,
        "--hand": '"Kalam", "Caveat", cursive',
      },
      sliders: {
        "--fx-opsz": "124",
        "--fx-wght": "600",
        "--fx-soft": "35",
        "--fx-wonk": "0.35",
        "--hand-size": "1.2rem",
        "--hand-rotate": "-1.2deg",
      },
    },
    {
      id: "archive",
      label: "Archive / Research Library",
      note: "The written brief: minimal archive-library vibes, warm neutral field with a butter-yellow and light-blue pop. Magazine (Fraunces) / Institution (IBM Plex Mono) / Note-taking (Kalam). Amber accent needs dark button text — on-honey is set for it.",
      tokens: {
        paper: "#f4f0e6",
        "paper-deep": "#eae3d4",
        card: "#fbf8f1",
        ink: "#22201c",
        "ink-soft": "#584f44",
        "ink-faint": "#8c8171",
        rule: "#dcd3c1",
        "rule-strong": "#c3b79f",
        butter: "#c08a2e",
        "butter-soft": "#faedcb",
        "on-butter": "#241c0c",
        blue: "#5c7fa3",
        "blue-soft": "#dbe5ef",
        plum: "#2e2a24",
        "on-plum": "#f4f0e6",
        error: "#a6402e",
      },
      stacks: {
        "--display": '"Fraunces", Georgia, serif',
        "--serif": SANS,
        "--mono": PLEX,
        "--hand": '"Kalam", "Caveat", cursive',
      },
      sliders: {
        "--fx-opsz": "90",
        "--fx-wght": "480",
        "--fx-soft": "25",
        "--fx-wonk": "0.25",
        "--hand-size": "1.1rem",
        "--hand-rotate": "-1deg",
      },
    },
    {
      id: "client-picks",
      label: "Asher's picks (free)",
      note: "His three Creative Market fonts through the closest free stand-ins: Promenade (calligraphic serif, titles) → Libre Bodoni; Makking (grotesk, paragraph) → Switzer; Paloma (hand-painted brush) → Permanent Marker. Swap in the purchased woff2s and only this preset changes.",
      tokens: {
        paper: "#f2ecdf",
        "paper-deep": "#e7dfd0",
        card: "#fbf6ec",
        ink: "#201915",
        "ink-soft": "#5c5248",
        "ink-faint": "#978b7c",
        rule: "#ddd3c1",
        "rule-strong": "#c0b29b",
        butter: "#a63a2e",
        "butter-soft": "#f2dbd4",
        "on-butter": "#fdf8ef",
        blue: "#3f5a44",
        "blue-soft": "#dde4db",
        plum: "#8a332f",
        "on-plum": "#f5eee1",
        error: "#a6402e",
      },
      stacks: {
        "--display": '"Libre Bodoni", "Playfair Display", Georgia, serif',
        "--serif": '"Switzer", "Inter", "Helvetica Neue", Arial, sans-serif',
        "--mono": PLEX,
        "--hand": '"Permanent Marker", "Kaushan Script", cursive',
      },
      sliders: {
        "--fx-opsz": "110",
        "--fx-wght": "500",
        "--fx-soft": "20",
        "--fx-wonk": "0.1",
        "--hand-size": "1.25rem",
        "--hand-rotate": "-2deg",
      },
    },
  ];

  var root = document.documentElement;
  var state = { tokens: {}, stacks: {}, sliders: {} };

  function cs(varName) {
    return getComputedStyle(root).getPropertyValue(varName).trim();
  }

  function readSaved() {
    try {
      return JSON.parse(localStorage.getItem(KEY) || "null");
    } catch (e) {
      return null;
    }
  }

  function save() {
    try {
      localStorage.setItem(KEY, JSON.stringify(state));
    } catch (e) {
      /* private mode — ignore */
    }
  }

  function setVar(name, value) {
    root.style.setProperty(name, value);
  }

  function stackFor(kind, key) {
    return STACKS[kind][key] || STACKS[kind][Object.keys(STACKS[kind])[0]];
  }

  function detectStack(kind, val) {
    var map = STACKS[kind];
    // Compare only the FIRST family of each stack. Searching the whole
    // string picks up fallbacks — "Libre Bodoni", "Playfair Display", …
    // would resolve to Playfair before Libre Bodoni was ever checked.
    function head(stack) {
      return (stack || "")
        .split(",")[0]
        .replace(/["']/g, "")
        .trim()
        .toLowerCase();
    }
    var wanted = head(val);
    for (var key in map) {
      if (head(map[key]) === wanted) return key;
    }
    return Object.keys(map)[0];
  }

  /* ---------- build palette UI ---------- */

  var swatches = document.getElementById("vibe-tokens");
  TOKENS.forEach(function (pair) {
    var name = pair[0];
    var label = pair[1];
    var wrap = document.createElement("label");
    wrap.className = "vibe-swatch";
    var input = document.createElement("input");
    input.type = "color";
    input.dataset.token = name;
    input.value = state.tokens[name] || cs("--" + name) || "#000000";
    var code = document.createElement("code");
    code.textContent = input.value;
    var text = document.createElement("span");
    text.textContent = label;
    text.style.flex = "1";
    wrap.appendChild(input);
    wrap.appendChild(text);
    wrap.appendChild(code);
    input.addEventListener("input", function () {
      var v = input.value;
      setVar("--" + name, v);
      code.textContent = v;
      state.tokens[name] = v;
      save();
    });
    swatches.appendChild(wrap);
  });

  /* ---------- type family selects ---------- */

  ["display", "body", "mono", "hand"].forEach(function (kind) {
    var varName = STACK_VARS[kind];
    var saved = state.stacks[varName];
    var sel = document.getElementById("vibe-sel-" + kind);
    sel.value = saved
      ? detectStack(kind, saved)
      : detectStack(kind, cs(varName));
    sel.addEventListener("change", function () {
      var stack = stackFor(kind, sel.value);
      setVar(varName, stack);
      state.stacks[varName] = stack;
      save();
    });
  });

  /* ---------- sliders ---------- */

  SLIDERS.forEach(function (spec) {
    var name = spec[0];
    var min = spec[2];
    var max = spec[3];
    var step = spec[4];
    var unit = spec[5];
    var input = document.getElementById("vibe-" + name);
    var out = document.getElementById("out-" + name);

    var current = state.sliders[name];
    if (current === undefined) {
      var raw = cs("--" + name);
      var num = parseFloat(raw);
      current =
        unit === "num100"
          ? num * 100
          : unit === "rem" || unit === "deg"
            ? num
            : num;
      if (isNaN(current)) current = unit === "num100" ? 60 : 50;
    }
    input.value = current;
    out.textContent = unit === "num100" ? Math.round(current) : current;

    input.addEventListener("input", function () {
      var v = parseFloat(input.value);
      var varValue;
      if (unit === "num100") varValue = String(v / 100); /* WONK 0-1 */
      else if (unit === "rem") varValue = v.toFixed(2) + "rem";
      else if (unit === "deg") varValue = v.toFixed(1) + "deg";
      else varValue = String(Math.round(v));
      setVar("--" + name, varValue);
      state.sliders[name] = v;
      out.textContent = unit === "num100" ? Math.round(v) : v;
      save();
    });
  });

  /* ---------- looks (presets) ---------- */

  function syncControls(st) {
    TOKENS.forEach(function (pair) {
      var input = swatches.querySelector('input[data-token="' + pair[0] + '"]');
      if (!input || !st.tokens || !st.tokens[pair[0]]) return;
      input.value = st.tokens[pair[0]];
      input.parentNode.querySelector("code").textContent = st.tokens[pair[0]];
    });
    ["display", "body", "mono", "hand"].forEach(function (kind) {
      var sel = document.getElementById("vibe-sel-" + kind);
      var stack = st.stacks && st.stacks[STACK_VARS[kind]];
      if (stack) sel.value = detectStack(kind, stack);
    });
    SLIDERS.forEach(function (spec) {
      var name = spec[0];
      var unit = spec[5];
      var raw = st.sliders && st.sliders["--" + name];
      if (raw === undefined) return;
      var value = unit === "num100" ? parseFloat(raw) * 100 : parseFloat(raw);
      document.getElementById("vibe-" + name).value = value;
      document.getElementById("out-" + name).textContent =
        unit === "num100" ? Math.round(value) : value;
    });
  }

  function applyState(st) {
    var key;
    if (st.tokens) for (key in st.tokens) setVar("--" + key, st.tokens[key]);
    if (st.stacks) for (key in st.stacks) setVar(key, st.stacks[key]);
    if (st.sliders) for (key in st.sliders) setVar("--" + key, st.sliders[key]);
  }

  var presetWrap = document.getElementById("vibe-presets");
  var presetNote = document.getElementById("vibe-preset-note");

  PRESETS.forEach(function (preset) {
    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "vibe-preset";
    btn.textContent = preset.label;
    btn.addEventListener("click", function () {
      state.tokens = JSON.parse(JSON.stringify(preset.tokens));
      state.stacks = JSON.parse(JSON.stringify(preset.stacks));
      state.sliders = JSON.parse(JSON.stringify(preset.sliders));
      applyState(state);
      syncControls(state);
      save();
      Array.prototype.forEach.call(presetWrap.children, function (el) {
        el.classList.toggle("is-active", el === btn);
      });
      presetNote.textContent = preset.note;
    });
    presetWrap.appendChild(btn);
  });

  /* ---------- drawer / fab ---------- */

  var fab = document.getElementById("vibe-fab");
  var panel = document.getElementById("vibe-panel");
  var closeBtn = document.getElementById("vibe-close");
  fab.addEventListener("click", function () {
    panel.hidden = false;
    fab.hidden = true;
  });
  closeBtn.addEventListener("click", function () {
    panel.hidden = true;
    fab.hidden = false;
  });

  /* ---------- export ---------- */

  function currentStacks() {
    var out = {};
    ["display", "body", "mono", "hand"].forEach(function (kind) {
      var sel = document.getElementById("vibe-sel-" + kind);
      out[STACK_VARS[kind]] = stackFor(kind, sel.value);
    });
    return out;
  }

  function currentSliders() {
    var out = {};
    SLIDERS.forEach(function (spec) {
      var name = spec[0];
      var unit = spec[5];
      var v = parseFloat(document.getElementById("vibe-" + name).value);
      if (unit === "num100") out["--" + name] = (v / 100).toFixed(2);
      else if (unit === "rem") out["--" + name] = v.toFixed(2) + "rem";
      else if (unit === "deg") out["--" + name] = v.toFixed(1) + "deg";
      else out["--" + name] = String(Math.round(v));
    });
    return out;
  }

  function buildExport() {
    var lines = [
      "/* preservation.studio — vibe lock-in */",
      "/* Paste this :root block into studio/static/studio/css/site.css */",
      ":root {",
    ];
    TOKENS.forEach(function (pair) {
      var input = swatches.querySelector('input[data-token="' + pair[0] + '"]');
      lines.push("  --" + pair[0] + ": " + input.value + ";");
    });
    var stacks = currentStacks();
    ["--serif", "--mono", "--display", "--hand"].forEach(function (v) {
      lines.push("  " + v + ": " + stacks[v] + ";");
    });
    var sliders = currentSliders();
    [
      "--fx-opsz",
      "--fx-wght",
      "--fx-soft",
      "--fx-wonk",
      "--hand-size",
      "--hand-rotate",
    ].forEach(function (v) {
      lines.push("  " + v + ": " + sliders[v] + ";");
    });
    lines.push("}");
    return lines.join("\n");
  }

  var exportBtn = document.getElementById("vibe-export");
  var modal = document.getElementById("vibe-modal");
  var cssArea = document.getElementById("vibe-css");
  var copyBtn = document.getElementById("vibe-copy");
  var closeModal = document.getElementById("vibe-close-modal");

  exportBtn.addEventListener("click", function () {
    cssArea.value = buildExport();
    modal.hidden = false;
    cssArea.focus();
    cssArea.select();
  });
  closeModal.addEventListener("click", function () {
    modal.hidden = true;
  });
  modal.addEventListener("click", function (e) {
    if (e.target === modal) modal.hidden = true;
  });
  copyBtn.addEventListener("click", function () {
    cssArea.select();
    var done = function () {
      copyBtn.textContent = "Copied";
      copyBtn.classList.add("copied");
      setTimeout(function () {
        copyBtn.textContent = "Copy";
        copyBtn.classList.remove("copied");
      }, 1500);
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(cssArea.value).then(done, done);
    } else {
      document.execCommand("copy");
      done();
    }
  });

  /* ---------- share link ---------- */

  function currentState() {
    var st = { tokens: {}, stacks: {}, sliders: {} };
    TOKENS.forEach(function (pair) {
      var input = swatches.querySelector('input[data-token="' + pair[0] + '"]');
      st.tokens[pair[0]] = input.value;
    });
    ["display", "body", "mono", "hand"].forEach(function (kind) {
      var sel = document.getElementById("vibe-sel-" + kind);
      st.stacks[STACK_VARS[kind]] = stackFor(kind, sel.value);
    });
    SLIDERS.forEach(function (spec) {
      var name = spec[0];
      var unit = spec[5];
      var v = parseFloat(document.getElementById("vibe-" + name).value);
      if (unit === "num100") st.sliders["--" + name] = (v / 100).toFixed(2);
      else if (unit === "rem") st.sliders["--" + name] = v.toFixed(2) + "rem";
      else if (unit === "deg") st.sliders["--" + name] = v.toFixed(1) + "deg";
      else st.sliders["--" + name] = String(Math.round(v));
    });
    return st;
  }

  function encodeState(st) {
    return btoa(JSON.stringify(st))
      .replace(/\+/g, "-")
      .replace(/\//g, "_")
      .replace(/=+$/, "");
  }

  var linkBtn = document.getElementById("vibe-link");
  linkBtn.addEventListener("click", function () {
    var url = location.pathname + "?vibe=1&t=" + encodeState(currentState());
    var done = function () {
      linkBtn.textContent = "Link copied";
      linkBtn.classList.add("copied");
      setTimeout(function () {
        linkBtn.textContent = "Copy Link";
        linkBtn.classList.remove("copied");
      }, 1500);
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(url).then(done, done);
    } else {
      var ta = document.createElement("textarea");
      ta.value = url;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      document.body.removeChild(ta);
      done();
    }
  });

  /* ---------- reset ---------- */

  document.getElementById("vibe-reset").addEventListener("click", function () {
    try {
      localStorage.removeItem(KEY);
    } catch (e) {}
    location.reload();
  });
})();
