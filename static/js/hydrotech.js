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

  // page head pictures: cross-fade to the next one every few seconds
  if (!window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    document.querySelectorAll(".slides").forEach(function (box) {
      var slides = box.querySelectorAll(".slide"), dots = box.querySelectorAll(".slides__dots span"), i = 0;
      if (slides.length < 2) return;
      setInterval(function () {
        if (document.hidden) return;
        slides[i].classList.remove("is-active"); if (dots[i]) dots[i].classList.remove("is-active");
        i = (i + 1) % slides.length;
        slides[i].classList.add("is-active"); if (dots[i]) dots[i].classList.add("is-active");
      }, 5500);
    });
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

// Videos: rail arrows, silent preview on hover, and the full-screen player.
(function () {
  var cards = Array.prototype.slice.call(document.querySelectorAll("[data-video]"));
  if (!cards.length) return;

  document.querySelectorAll("[data-rail]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var track = document.querySelector("[data-rail-track]");
      if (track) track.scrollBy({ left: parseInt(btn.getAttribute("data-rail"), 10) * track.clientWidth * 0.8, behavior: "smooth" });
    });
  });

  // uploaded videos with no cover picture play silently while the pointer is over them
  if (window.matchMedia("(hover: hover)").matches) {
    cards.forEach(function (card) {
      var v = card.querySelector(".vcard__media video");
      if (!v) return;
      card.addEventListener("mouseenter", function () { var p = v.play(); if (p && p.catch) p.catch(function () {}); });
      card.addEventListener("mouseleave", function () { v.pause(); });
    });
  }

  var player = document.getElementById("vplayer");
  if (!player) return;
  var frame = player.querySelector(".vplayer__frame");
  var title = player.querySelector(".vplayer__title");
  var text = player.querySelector(".vplayer__text");
  var index = 0, lastFocus = null;

  function load(i) {
    index = (i + cards.length) % cards.length;
    var c = cards[index], kind = c.getAttribute("data-kind"), src = c.getAttribute("data-src");
    Array.prototype.slice.call(frame.children).forEach(function (el) { if (!el.classList.contains("vplayer__wm")) el.remove(); });
    player.classList.toggle("vplayer--embed", kind !== "file");
    if (kind === "file") {
      var v = document.createElement("video");
      v.src = src; v.controls = true; v.autoplay = true; v.playsInline = true; v.setAttribute("playsinline", "");
      frame.appendChild(v);
    } else {
      var f = document.createElement("iframe");
      f.src = src; f.title = c.getAttribute("data-title");
      f.allow = "autoplay; encrypted-media; picture-in-picture; fullscreen; clipboard-write";
      f.allowFullscreen = true;
      f.referrerPolicy = "strict-origin-when-cross-origin";
      frame.appendChild(f);
    }
    player.classList.toggle("vplayer--tall", c.getAttribute("data-vertical") === "1");
    title.textContent = c.getAttribute("data-title");
    text.textContent = c.getAttribute("data-text") || "";
  }
  function open(i) {
    lastFocus = document.activeElement;
    player.classList.toggle("vplayer--single", cards.length < 2);
    load(i);
    player.hidden = false;
    document.body.classList.add("modal-open");
    requestAnimationFrame(function () { player.classList.add("open"); });
    player.querySelector(".vplayer__close").focus();
  }
  function close() {
    player.classList.remove("open");
    document.body.classList.remove("modal-open");
    setTimeout(function () {  // removing the player stops the sound
      player.hidden = true;
      Array.prototype.slice.call(frame.children).forEach(function (el) { if (!el.classList.contains("vplayer__wm")) el.remove(); });
    }, 300);
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  }

  cards.forEach(function (card, i) { card.addEventListener("click", function () { open(i); }); });
  player.addEventListener("click", function (e) {
    var act = e.target.closest("[data-vp]");
    if (act) {
      var a = act.getAttribute("data-vp");
      if (a === "close") close(); else load(index + (a === "next" ? 1 : -1));
    } else if (e.target === player) close();
  });
  document.addEventListener("keydown", function (e) {
    if (player.hidden) return;
    if (e.key === "Escape") close();
    if (e.key === "ArrowRight") load(index + 1);
    if (e.key === "ArrowLeft") load(index - 1);
  });
})();
