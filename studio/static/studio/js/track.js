/* ============================================================
   preservation.studio — scene track navigation
   ============================================================

   The home page lays its scenes out side by side in a native
   horizontal scroller. This only adds the affordances the browser
   does not give you for free: prev/next buttons, arrow keys, and a
   scene counter.

   It never hijacks the wheel or traps the page — scrolling still
   works exactly as the browser does it, and every scene's content
   is reachable by ordinary scrolling (and stacks vertically under
   900px, where this file does nothing).
   ============================================================ */

(function () {
  "use strict";

  var track = document.getElementById("track");
  if (!track) return;

  var scenes = Array.prototype.slice.call(track.querySelectorAll(".scene"));
  if (scenes.length < 2) return;

  var counter = document.querySelector("[data-scene-now]");
  var pad = function (n) {
    return (n < 10 ? "0" : "") + n;
  };

  // Index of the scene nearest the left edge of the viewport.
  function currentIndex() {
    var best = 0;
    var bestGap = Infinity;
    scenes.forEach(function (scene, i) {
      var gap = Math.abs(scene.offsetLeft - track.scrollLeft);
      if (gap < bestGap) {
        bestGap = gap;
        best = i;
      }
    });
    return best;
  }

  function goTo(i) {
    var target = scenes[Math.max(0, Math.min(scenes.length - 1, i))];
    if (!target) return;
    track.scrollTo({ left: target.offsetLeft, behavior: "smooth" });
  }

  function sync() {
    var i = currentIndex();
    if (counter) counter.textContent = pad(i + 1);
    document.querySelectorAll("[data-track-prev]").forEach(function (b) {
      b.disabled = i === 0;
    });
    document.querySelectorAll("[data-track-next]").forEach(function (b) {
      b.disabled = i === scenes.length - 1;
    });
  }

  document.querySelectorAll("[data-track-prev]").forEach(function (b) {
    b.addEventListener("click", function () {
      goTo(currentIndex() - 1);
    });
  });
  document.querySelectorAll("[data-track-next]").forEach(function (b) {
    b.addEventListener("click", function () {
      goTo(currentIndex() + 1);
    });
  });

  // Arrow keys, but only when the user is not typing in a form control and
  // not reading a vertical (stacked) layout.
  document.addEventListener("keydown", function (e) {
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    var el = document.activeElement;
    if (el && /^(INPUT|TEXTAREA|SELECT)$/.test(el.tagName)) return;
    if (window.matchMedia("(max-width: 900px)").matches) return;
    if (e.key === "ArrowRight") {
      e.preventDefault();
      goTo(currentIndex() + 1);
    } else if (e.key === "ArrowLeft") {
      e.preventDefault();
      goTo(currentIndex() - 1);
    }
  });

  var raf = null;
  track.addEventListener("scroll", function () {
    if (raf) return;
    raf = window.requestAnimationFrame(function () {
      raf = null;
      sync();
    });
  });

  window.addEventListener("resize", sync);

  // Keep the browser's own scroll restoration from landing mid-track with a
  // stale counter.
  if ("scrollRestoration" in window.history) {
    window.history.scrollRestoration = "manual";
  }

  sync();
})();
