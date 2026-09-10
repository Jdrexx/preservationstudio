/* ============================================================
   preservation.studio — the welcome gate
   ============================================================

   The entry screen, replicated from rabenrifaie.com: a full-bleed
   surface, a small progress bar dead centre that fills while a
   percentage counts up bottom-right, and at 100% the bar is
   replaced by the wordmark with a pill-outlined "Welcome" beneath
   it. Click and the site opens.

   The gate is markup-first, so this file only drives the states:

     (none)      counting — bar filling, counter ticking
     is-ready    bar gone, wordmark + Welcome shown and focusable
     is-leaving  fading out, then the node is removed for good

   Three things here are deliberate and not in the reference:

     · `open` / the button's `disabled` attribute keep the gate from
       being dismissed before it is ready to be dismissed.
     · leaving removes the node entirely rather than leaving a
       z-index-90 overlay hidden over the page — a hidden overlay is
       still a trap for screen readers and for pointer events.
     · any click, plus Enter/Space/Escape, opens the site. The
       reference accepts only a click on the word itself.

   The no-JS and never-initialised cases are handled in CSS (a
   <noscript> rule and a failsafe animation), not here — if this
   file never runs, nothing here can help.
   ============================================================ */

(function () {
  "use strict";

  var gate = document.getElementById("welcome");
  if (!gate) return;

  var bar = document.getElementById("welcome-bar");
  var name = document.getElementById("welcome-name");
  var count = document.getElementById("welcome-count");
  var enter = document.getElementById("welcome-enter");
  var track = document.getElementById("track");
  var body = document.body;
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)");

  var COUNT_MS = 1200;
  var FADE_MS = 600;
  var open = true;

  // Tell the stylesheet the script is alive: this cancels the failsafe
  // animation that would otherwise clear the gate on its own.
  gate.classList.add("is-live");
  body.classList.add("is-welcome");

  function setPercent(ratio) {
    var pct = Math.round(ratio * 100);
    if (count) count.textContent = pct;
    // The bar IS the wordmark: --fill sizes the solid layer that is clipped to
    // its glyphs, anchored centre so it grows outward through the letters.
    if (name) name.style.setProperty("--fill", pct + "%");
    if (bar) bar.setAttribute("aria-valuenow", pct);
  }

  function ready() {
    setPercent(1);
    gate.classList.add("is-ready");
    if (enter) {
      enter.disabled = false;
      try {
        enter.focus({ preventScroll: true });
      } catch (err) {
        enter.focus();
      }
    }
  }

  function countUp() {
    if (reduce.matches || COUNT_MS === 0) {
      ready();
      return;
    }
    var start = null;
    function step(now) {
      if (start === null) start = now;
      var ratio = Math.min(1, (now - start) / COUNT_MS);
      setPercent(ratio);
      if (ratio < 1) {
        window.requestAnimationFrame(step);
      } else {
        ready();
      }
    }
    window.requestAnimationFrame(step);
  }

  function finish() {
    if (gate.parentNode) gate.parentNode.removeChild(gate);
    body.classList.remove("is-welcome");
    // Land focus somewhere real, so the track is usable from the keyboard.
    var first = document.querySelector("[data-scene-link]");
    if (first) first.focus({ preventScroll: true });
  }

  function leave() {
    if (!open) return;
    open = false;
    gate.classList.add("is-leaving");
    if (reduce.matches) {
      finish();
    } else {
      window.setTimeout(finish, FADE_MS);
    }
  }

  gate.addEventListener("click", leave);

  document.addEventListener("keydown", function (e) {
    if (!open) return;
    if (
      e.key !== "Enter" &&
      e.key !== " " &&
      e.key !== "Spacebar" &&
      e.key !== "Escape"
    )
      return;
    // Act on the key here rather than relying on the focused button's own
    // activation: leave() is idempotent, so a click that also fires is
    // harmless, and the gate then opens on Enter/Space in every host.
    e.preventDefault();
    if (enter && !enter.disabled) leave();
  });

  // A visitor who starts scrolling or swiping is telling us they are done
  // looking at the gate — but only once it is actually ready to leave.
  ["wheel", "touchstart"].forEach(function (type) {
    window.addEventListener(
      type,
      function () {
        if (open && enter && !enter.disabled) leave();
      },
      { passive: true },
    );
  });

  countUp();
})();
