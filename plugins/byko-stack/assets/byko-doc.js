/* byko-doc.js — 읽기 보조. 없어도 문서는 전부 읽힌다(모든 장치가 점진적 향상). */
(function () {
  "use strict";

  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* --- 등장 애니메이션 ---------------------------------------------------- */
  var reveals = document.querySelectorAll(".reveal");
  if (reveals.length && "IntersectionObserver" in window && !reduce) {
    document.body.classList.add("js-anim");
    var ro = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add("in"); ro.unobserve(e.target); }
      });
    }, { rootMargin: "0px 0px -12% 0px", threshold: .05 });
    for (var i = 0; i < reveals.length; i++) ro.observe(reveals[i]);
  }

  /* --- 읽기 진행률 -------------------------------------------------------- */
  var bar = document.querySelector(".progress > span");
  /* --- 챕터 네비 활성 표시 ------------------------------------------------ */
  var navLinks = document.querySelectorAll(".chapnav a[href^='#']");
  var chapters = [];
  for (var j = 0; j < navLinks.length; j++) {
    var el = document.getElementById(decodeURIComponent(navLinks[j].getAttribute("href").slice(1)));
    if (el) chapters.push({ link: navLinks[j], el: el });
  }

  function onScroll() {
    if (bar) {
      var h = document.documentElement.scrollHeight - window.innerHeight;
      bar.style.width = (h > 0 ? Math.min(100, (window.scrollY / h) * 100) : 0) + "%";
    }
    if (chapters.length) {
      var mark = window.scrollY + window.innerHeight * 0.3;
      var cur = chapters[0];
      for (var k = 0; k < chapters.length; k++) {
        if (chapters[k].el.offsetTop <= mark) cur = chapters[k];
      }
      for (var m = 0; m < chapters.length; m++) {
        chapters[m].link.classList.toggle("active", chapters[m] === cur);
      }
      if (cur && cur.link.scrollIntoView && cur.link.parentNode.parentNode.scrollWidth > window.innerWidth) {
        var navBox = cur.link.parentNode.parentNode;
        var want = cur.link.offsetLeft - navBox.clientWidth / 2 + cur.link.clientWidth / 2;
        navBox.scrollTo({ left: want, behavior: reduce ? "auto" : "smooth" });
      }
    }
  }
  var ticking = false;
  window.addEventListener("scroll", function () {
    if (ticking) return;
    ticking = true;
    window.requestAnimationFrame(function () { onScroll(); ticking = false; });
  }, { passive: true });
  onScroll();

  /* --- 시나리오 탭 (AC를 눌러 보는 장치) ---------------------------------- */
  var scenarios = document.querySelectorAll(".scenario");
  for (var s = 0; s < scenarios.length; s++) {
    (function (root) {
      var btns = root.querySelectorAll(".scn-btn");
      var panels = root.querySelectorAll(".scn-panel");
      function select(idx) {
        for (var b = 0; b < btns.length; b++) btns[b].setAttribute("aria-selected", String(b === idx));
        for (var p = 0; p < panels.length; p++) panels[p].hidden = p !== idx;
      }
      for (var b2 = 0; b2 < btns.length; b2++) {
        (function (n) { btns[n].addEventListener("click", function () { select(n); }); })(b2);
      }
      select(0);
    })(scenarios[s]);
  }

  /* --- 도구 막대 ---------------------------------------------------------- */
  var bar2 = document.querySelector(".toolbar");
  if (bar2) {
    var KEY = "byko-doc-theme";
    var saved = null;
    try { saved = localStorage.getItem(KEY); } catch (e) {}
    if (saved) document.documentElement.setAttribute("data-theme", saved);

    function button(label, fn) {
      var b = document.createElement("button");
      b.type = "button";
      b.textContent = label;
      b.addEventListener("click", function () { fn(b); });
      bar2.appendChild(b);
      return b;
    }
    button("밝게 / 어둡게", function () {
      var next = document.documentElement.getAttribute("data-theme") === "light" ? null : "light";
      if (next) document.documentElement.setAttribute("data-theme", next);
      else document.documentElement.removeAttribute("data-theme");
      try { next ? localStorage.setItem(KEY, next) : localStorage.removeItem(KEY); } catch (e) {}
    });
    if (document.querySelector("details.agent-only")) {
      button("에이전트용 영역 펼치기", function (b) {
        var ds = document.querySelectorAll("details.agent-only");
        var open = b.textContent.indexOf("펼치기") >= 0;
        for (var d = 0; d < ds.length; d++) ds[d].open = open;
        b.textContent = open ? "에이전트용 영역 접기" : "에이전트용 영역 펼치기";
      });
    }
    button("인쇄", function () {
      var ds = document.querySelectorAll("details");
      for (var d = 0; d < ds.length; d++) ds[d].open = true;
      window.print();
    });
  }

  /* --- 결정 목록에서 점프하면 잠깐 강조 ----------------------------------- */
  document.addEventListener("click", function (e) {
    var a = e.target.closest ? e.target.closest(".decisions a") : null;
    if (!a) return;
    var el = document.getElementById(decodeURIComponent((a.getAttribute("href") || "").slice(1)));
    if (!el) return;
    var d = el.closest ? el.closest("details") : null;
    if (d) d.open = true;
  });
})();
