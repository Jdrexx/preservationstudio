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
    ["blue", "Blue"],
    ["blue-soft", "Blue soft"],
    ["plum", "Plum"],
    ["on-plum", "On plum"],
    ["error", "Error"],
  ];

  var STACKS = {
    display: {
      fraunces: '"Fraunces", Georgia, serif',
      georgia: "Georgia, serif",
    },
    body: {
      newsreader: '"Newsreader", Georgia, "Times New Roman", serif',
      fraunces: '"Fraunces", Georgia, serif',
      georgia: "Georgia, serif",
    },
    mono: {
      plex: '"IBM Plex Mono", "Courier New", monospace',
      courier: '"Courier New", monospace',
    },
    hand: {
      kalam: '"Kalam", "Caveat", cursive',
      caveat: '"Caveat", cursive',
    },
  };

  var STACK_VARS = { display: "--display", body: "--serif", mono: "--mono", hand: "--hand" };

  var SLIDERS = [
    ["fx-wonk", "WONK (wonkiness)", 0, 100, 1, "num100"],
    ["fx-soft", "SOFT (roundness)", 0, 100, 1, "num"],
    ["fx-opsz", "Optical size", 9, 144, 1, "num"],
    ["fx-wght", "Display weight", 100, 900, 1, "num"],
    ["hand-size", "Note size", 0.8, 1.6, 0.05, "rem"],
    ["hand-rotate", "Note tilt", -5, 5, 0.1, "deg"],
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
    val = (val || "").toLowerCase();
    for (var key in map) {
      var probe = map[key].toLowerCase();
      var first = probe.split(",")[0].replace(/["']/g, "").trim();
      if (val.indexOf(first) !== -1) return key;
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
    sel.value = saved ? detectStack(kind, saved) : detectStack(kind, cs(varName));
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
      current = unit === "num100" ? num * 100 : unit === "rem" || unit === "deg" ? num : num;
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
    ["--fx-opsz", "--fx-wght", "--fx-soft", "--fx-wonk", "--hand-size", "--hand-rotate"].forEach(
      function (v) {
        lines.push("  " + v + ": " + sliders[v] + ";");
      }
    );
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
    return btoa(JSON.stringify(st)).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
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
