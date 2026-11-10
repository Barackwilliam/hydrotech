(function () {
  document.documentElement.classList.add("js");

  // year in the footer
  document.querySelectorAll("[data-year]").forEach(function (el) { el.textContent = new Date().getFullYear(); });

  // header: transparent over the dark top of the page, solid once the page scrolls
  var header = document.querySelector(".header");
  function onScroll() { if (header) header.classList.toggle("is-scrolled", window.scrollY > 24); }
  onScroll();
  window.addEventListener("scroll", onScroll, { passive: true });

  // mobile menu (full screen)
  var toggle = document.querySelector(".nav-toggle");
  var nav = document.getElementById("nav");
  if (toggle && nav) {
    var menuIcon = toggle.innerHTML;
    var closeIcon = '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M6 6l12 12M18 6 6 18"/></svg>';
    function setNav(open) {
      nav.classList.toggle("open", open);
      document.body.classList.toggle("nav-open", open);
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
      toggle.innerHTML = open ? closeIcon : menuIcon;
    }
    toggle.addEventListener("click", function () { setNav(!nav.classList.contains("open")); });
    nav.addEventListener("click", function (e) { if (e.target.closest("a")) setNav(false); });
    document.addEventListener("keydown", function (e) { if (e.key === "Escape" && nav.classList.contains("open")) setNav(false); });
  }

  // messages slide away after a while
  document.querySelectorAll(".toast").forEach(function (t) {
    setTimeout(function () { t.classList.add("is-gone"); setTimeout(function () { t.remove(); }, 450); }, 7000);
  });

  // numbers count up when they come into view
  var counters = document.querySelectorAll("[data-count]");
  function countUp(el) {
    var end = parseInt(el.getAttribute("data-count"), 10) || 0, start = performance.now(), dur = 1200;
    (function step(now) {
      var k = Math.min(1, (now - start) / dur);
      el.textContent = Math.round(end * (1 - Math.pow(1 - k, 3)));
      if (k < 1) requestAnimationFrame(step);
    })(start);
  }
  if ("IntersectionObserver" in window && !window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    var co = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) { if (en.isIntersecting) { countUp(en.target); co.unobserve(en.target); } });
    }, { threshold: .6 });
    counters.forEach(function (el) { co.observe(el); });
  }

  // reveal on scroll
  var items = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) { if (en.isIntersecting) { en.target.classList.add("in"); io.unobserve(en.target); } });
    }, { rootMargin: "0px 0px -40px 0px" });
    items.forEach(function (el) { io.observe(el); });
  } else {
    items.forEach(function (el) { el.classList.add("in"); });
  }

  // project filters
  document.querySelectorAll(".filter").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var f = btn.getAttribute("data-filter");
      document.querySelectorAll(".filter").forEach(function (b) { b.classList.toggle("active", b === btn); });
      document.querySelectorAll(".gallery__item").forEach(function (it) {
        it.classList.toggle("is-hidden", f !== "all" && it.getAttribute("data-group") !== f);
      });
    });
  });

  // lightbox
  var links = Array.prototype.slice.call(document.querySelectorAll("[data-lightbox]"));
  if (!links.length) return;
  var box = document.createElement("div");
  box.className = "lightbox";
  box.setAttribute("role", "dialog");
  box.setAttribute("aria-modal", "true");
  box.innerHTML = '<button class="lb-close" aria-label="Close">&times;</button>' +
    '<button class="lb-prev" aria-label="Previous">&#8249;</button><img alt=""><p></p>' +
    '<button class="lb-next" aria-label="Next">&#8250;</button>';
  document.body.appendChild(box);
  var img = box.querySelector("img"), cap = box.querySelector("p"), index = 0;

  function visible() { return links.filter(function (l) { return !l.classList.contains("is-hidden"); }); }
  function show(i) {
    var list = visible();
    index = (i + list.length) % list.length;
    img.src = list[index].getAttribute("href");
    img.alt = cap.textContent = list[index].getAttribute("data-caption") || "";
    box.classList.add("open");
  }
  function close() { box.classList.remove("open"); img.src = ""; }

  links.forEach(function (l) {
    l.addEventListener("click", function (e) { e.preventDefault(); show(visible().indexOf(l)); });
  });
  box.querySelector(".lb-close").addEventListener("click", close);
  box.querySelector(".lb-prev").addEventListener("click", function () { show(index - 1); });
  box.querySelector(".lb-next").addEventListener("click", function () { show(index + 1); });
  box.addEventListener("click", function (e) { if (e.target === box) close(); });
  document.addEventListener("keydown", function (e) {
    if (!box.classList.contains("open")) return;
    if (e.key === "Escape") close();
    if (e.key === "ArrowLeft") show(index - 1);
    if (e.key === "ArrowRight") show(index + 1);
  });
})();

// First visit: ask for the language once the page has finished loading, and remember the answer.
(function () {
  var modal = document.getElementById("lang-modal");
  if (!modal) return;
  var current = document.documentElement.lang || "sw";
  var lastFocus = null;

  function remember(lang) {
    document.cookie = "lang=" + lang + "; max-age=31536000; path=/; samesite=lax";
  }
  function open() {
    lastFocus = document.activeElement;
    modal.hidden = false;
    document.body.classList.add("modal-open");
    requestAnimationFrame(function () { modal.classList.add("open"); });
    var first = modal.querySelector('[data-lang-pick="' + current + '"].lang-option') || modal.querySelector(".lang-option");
    if (first) first.focus();
  }
  function close() {
    modal.classList.remove("open");
    document.body.classList.remove("modal-open");
    setTimeout(function () { modal.hidden = true; }, 250);
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  }

  modal.addEventListener("click", function (e) {
    var pick = e.target.closest("[data-lang-pick]");
    if (pick) {
      var lang = pick.getAttribute("data-lang-pick");
      remember(lang);
      // same language as the page: just close; the other one: follow the link to reload in that language
      if (lang === current) { e.preventDefault(); close(); }
      return;
    }
    if (e.target === modal) { remember(current); close(); }
  });
  document.addEventListener("keydown", function (e) {
    if (modal.hidden) return;
    if (e.key === "Escape") { remember(current); close(); }
    if (e.key === "Tab") {  // keep focus inside the popup
      var items = modal.querySelectorAll("a, button");
      var firstEl = items[0], lastEl = items[items.length - 1];
      if (e.shiftKey && document.activeElement === firstEl) { e.preventDefault(); lastEl.focus(); }
      else if (!e.shiftKey && document.activeElement === lastEl) { e.preventDefault(); firstEl.focus(); }
    }
  });

  function later() { setTimeout(open, 500); }
  if (document.readyState === "complete") later();
  else window.addEventListener("load", later);
})();
