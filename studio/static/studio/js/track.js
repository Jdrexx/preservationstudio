/* ============================================================
   preservation.studio — scene track navigation
   ============================================================

   The home page is ONE page: full-viewport scenes laid out side by
   side in a native horizontal scroller, the page itself clipped so
   nothing scrolls vertically. This file adds what the browser does
   not give for free:

     · the scene bar (a link per scene, the counter, prev/next)
     · the reference's circular "explore" control, which advances a
       scene and wraps at the end
     · arrow keys, Home/End
     · the hash — /#intensive opens the Intensive scene, and sliding
       the track keeps the hash in step without stacking history

   Every scene is one viewport wide at every breakpoint, so the
   track maths is simply "index x viewport width". Scrolling stays a
   real scroll: trackpad, touch and the scrollbar all behave.
   ============================================================ */

(function () {
  "use strict";

  var track = document.getElementById("track");
  if (!track) return;

  var scenes = Array.prototype.slice.call(track.querySelectorAll(".scene"));
  if (scenes.length < 2) return;

  var counter = document.querySelector("[data-scene-now]");
  var total = document.querySelector("[data-scene-total]");
  var menuLinks = Array.prototype.slice.call(
    document.querySelectorAll("[data-scene-link]"),
  );
  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

  // Until the deep link has been honoured the track must not rewrite the
  // hash: on a cold load the scenes can still report offsetLeft 0, and a
  // sync() from there would scroll to the first scene AND overwrite the URL
  // with #home, silently destroying the link the visitor arrived on.
  var initialised = false;
  // The scene the track is supposed to be on, so it can be re-anchored once
  // layout has definitely settled.
  var intended = 0;

  var pad = function (n) {
    return (n < 10 ? "0" : "") + n;
  };

  if (total) total.textContent = pad(scenes.length);

  // A scene is exactly one viewport wide, so index x viewport width is the
  // position even before layout has settled enough to report offsetLeft.
  function leftFor(i) {
    return scenes[i].offsetLeft || i * track.clientWidth;
  }

  // Index of the scene nearest the left edge of the viewport.
  function currentIndex() {
    var best = 0;
    var bestGap = Infinity;
    scenes.forEach(function (scene, i) {
      var gap = Math.abs(leftFor(i) - track.scrollLeft);
      if (gap < bestGap) {
        bestGap = gap;
        best = i;
      }
    });
    return best;
  }

  function indexOfId(id) {
    for (var i = 0; i < scenes.length; i++) {
      if (scenes[i].id === id) return i;
    }
    return -1;
  }

  function goTo(i, instant) {
    var idx = Math.max(0, Math.min(scenes.length - 1, i));
    if (!scenes[idx]) return;
    intended = idx;
    var left = leftFor(idx);
    if (instant || reduceMotion.matches) {
      // `scroll-behavior: smooth` applies to direct assignments too, so a
      // "jump" would still animate and race the browser's own fragment
      // scroll on a cold load. Turn it off for the assignment.
      var previous = track.style.scrollBehavior;
      track.style.scrollBehavior = "auto";
      track.scrollLeft = left;
      track.style.scrollBehavior = previous;
    } else {
      track.scrollTo({ left: left, behavior: "smooth" });
    }
  }

  // Keep the URL in step with the scene, without stacking history entries:
  // the back button should leave the page, not walk the track.
  function setHash(id) {
    if (!initialised || !id) return;
    if ("#" + id === window.location.hash) return;
    if (window.history && window.history.replaceState) {
      window.history.replaceState(null, "", "#" + id);
    }
  }

  function sync() {
    var i = currentIndex();
    if (counter) counter.textContent = pad(i + 1);

    menuLinks.forEach(function (link) {
      var href = link.getAttribute("href") || "";
      if (href === "#" + scenes[i].id) {
        link.setAttribute("aria-current", "true");
      } else {
        link.removeAttribute("aria-current");
      }
    });

    var atEnd = i === scenes.length - 1;
    document.querySelectorAll("[data-track-prev]").forEach(function (b) {
      b.disabled = i === 0;
    });
    document.querySelectorAll("[data-track-next]").forEach(function (b) {
      b.disabled = atEnd;
    });

    setHash(scenes[i].id);
  }

  function step(delta, wrap) {
    var next = currentIndex() + delta;
    if (wrap) next = (next + scenes.length) % scenes.length;
    goTo(next);
  }

  menuLinks.forEach(function (link) {
    link.addEventListener("click", function (e) {
      var i = indexOfId((link.getAttribute("href") || "").replace("#", ""));
      if (i < 0) return;
      e.preventDefault();
      goTo(i);
    });
  });

  document.querySelectorAll("[data-track-prev]").forEach(function (b) {
    b.addEventListener("click", function () {
      step(-1, false);
    });
  });
  document.querySelectorAll("[data-track-next]").forEach(function (b) {
    b.addEventListener("click", function () {
      step(1, false);
    });
  });
  document.querySelectorAll("[data-explore]").forEach(function (b) {
    b.addEventListener("click", function () {
      step(1, true);
    });
  });

  // Arrow keys / Home / End, but never while the user is typing in a form and
  // never while the welcome gate is still up — the gate owns the keyboard.
  document.addEventListener("keydown", function (e) {
    if (document.body.classList.contains("is-welcome")) return;
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    var el = document.activeElement;
    if (el && /^(INPUT|TEXTAREA|SELECT)$/.test(el.tagName)) return;
    if (e.key === "ArrowRight") {
      e.preventDefault();
      step(1, false);
    } else if (e.key === "ArrowLeft") {
      e.preventDefault();
      step(-1, false);
    } else if (e.key === "Home") {
      e.preventDefault();
      goTo(0);
    } else if (e.key === "End") {
      e.preventDefault();
      goTo(scenes.length - 1);
    }
  });

  // A deep link (#intensive) opens that scene, and Back/Forward through the
  // hash moves the track rather than the page.
  window.addEventListener("hashchange", function () {
    if (!initialised) return;
    var i = indexOfId((window.location.hash || "").replace("#", ""));
    if (i >= 0) goTo(i);
  });

  // Someone dragging or swiping the track themselves must still move the
  // counter, the active word and the hash with them.
  var raf = null;
  track.addEventListener("scroll", function () {
    if (raf) return;
    raf = window.requestAnimationFrame(function () {
      raf = null;
      sync();
    });
  });

  window.addEventListener("resize", function () {
    // Scene widths are viewport-relative, so re-anchor after a resize.
    goTo(intended, true);
    sync();
  });

  if ("scrollRestoration" in window.history) {
    window.history.scrollRestoration = "manual";
  }

  function applyInitial() {
    var i = indexOfId((window.location.hash || "").replace("#", ""));
    initialised = true;
    goTo(i < 0 ? intended : i, true);
    sync();
  }

  // Position before first paint, then again when layout has settled.
  applyInitial();
  window.requestAnimationFrame(function () {
    applyInitial();
    sync();
  });
  window.addEventListener("load", function () {
    applyInitial();
    sync();
  });
})();
