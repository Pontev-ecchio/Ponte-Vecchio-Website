(function () {
  // "Jetzt geöffnet" – berechnet in Regensburger Zeit aus den Öffnungszeiten im Admin-Bereich
  var dataEl = document.getElementById("hours-data");
  if (dataEl) {
    try {
      var D = JSON.parse(dataEl.textContent), H = D.h, N = D.n;
      var fmt = function (m) { return String(Math.floor(m / 60)).padStart(2, "0") + ":" + String(m % 60).padStart(2, "0"); };
      var parts = new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/Berlin", weekday: "short", hour: "2-digit", minute: "2-digit", hourCycle: "h23" }).formatToParts(new Date());
      var get = function (t) { return parts.find(function (p) { return p.type === t; }).value; };
      var d = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].indexOf(get("weekday"));
      var now = parseInt(get("hour"), 10) * 60 + parseInt(get("minute"), 10);
      var row = document.querySelector('.hours tr[data-day="' + d + '"]');
      if (row) row.classList.add("today");
      var st = document.getElementById("status");
      if (st) {
        var b = st.querySelector("b"), s = st.querySelector("span");
        var cur = (H[d] || []).find(function (r) { return now >= r[0] && now < r[1]; });
        if (cur) { st.classList.add("open"); b.textContent = "Jetzt geöffnet"; s.textContent = "Heute bis " + fmt(cur[1]) + " Uhr"; }
        else {
          b.textContent = "Gerade geschlossen";
          var next = (H[d] || []).find(function (r) { return r[0] > now; });
          if (next) s.textContent = "Heute ab " + fmt(next[0]) + " Uhr";
          else {
            for (var i = 1; i <= 7; i++) {
              var nd = (d + i) % 7;
              if (H[nd] && H[nd].length) { s.textContent = (i === 1 ? "Morgen" : N[nd]) + " ab " + fmt(H[nd][0][0]) + " Uhr"; break; }
            }
          }
        }
      }
    } catch (e) {}
  }

  // Speisekarte: aktive Kategorie in der Leiste markieren
  var links = {};
  document.querySelectorAll(".menu-nav a").forEach(function (a) { links[a.getAttribute("href").slice(1)] = a; });
  if (Object.keys(links).length && "IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (en) {
        if (!en.isIntersecting) return;
        Object.keys(links).forEach(function (k) { links[k].classList.remove("on"); });
        var l = links[en.target.id];
        if (l) { l.classList.add("on"); var p = l.parentElement; p.scrollTo({ left: l.offsetLeft - p.clientWidth / 2 + l.clientWidth / 2, behavior: "smooth" }); }
      });
    }, { rootMargin: "-45% 0px -50% 0px" });
    document.querySelectorAll(".cat").forEach(function (c) { io.observe(c); });
  }

  // Cookie-Banner + Meta Pixel (lädt NUR nach Zustimmung)
  var cfgEl = document.getElementById("consent-cfg"), cc = document.getElementById("cc");
  if (cfgEl && cc) {
    var PIX = "";
    try { PIX = JSON.parse(cfgEl.textContent).pixel || ""; } catch (e) {}
    var KEY = "pv-consent-v1";
    var read = function () { try { return localStorage.getItem(KEY); } catch (e) { return null; } };
    var save = function (v) { try { localStorage.setItem(KEY, v); } catch (e) {} };
    var loaded = false;
    var loadPixel = function () {
      if (loaded || !PIX) return;
      loaded = true;
      /* Offizieller Meta-Pixel-Code */
      !function (f, b, e, v, n, t, s) {
        if (f.fbq) return; n = f.fbq = function () { n.callMethod ? n.callMethod.apply(n, arguments) : n.queue.push(arguments); };
        if (!f._fbq) f._fbq = n; n.push = n; n.loaded = !0; n.version = "2.0"; n.queue = [];
        t = b.createElement(e); t.async = !0; t.src = v; s = b.getElementsByTagName(e)[0]; s.parentNode.insertBefore(t, s);
      }(window, document, "script", "https://connect.facebook.net/en_US/fbevents.js");
      window.fbq("init", PIX);
      window.fbq("track", "PageView");
    };
    var show = function () { cc.hidden = false; };
    var choice = read();
    if (choice === "yes") loadPixel(); else if (choice !== "no") show();
    document.addEventListener("click", function (ev) {
      var t = ev.target.closest("[data-cc]");
      if (t) {
        var a = t.getAttribute("data-cc");
        if (a === "open") { show(); return; }
        save(a); cc.hidden = true;
        if (a === "yes") loadPixel();
        else {
          // Widerruf: Meta-Cookies löschen, ggf. Seite ohne Pixel neu laden
          ["_fbp", "_fbc"].forEach(function (n) {
            var host = location.hostname, parts = host.split("."), doms = [""];
            for (var i = 0; i < parts.length - 1; i++) doms.push("; domain=." + parts.slice(i).join("."));
            doms.forEach(function (d) { document.cookie = n + "=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/" + d; });
          });
          if (loaded) location.reload();
        }
        return;
      }
      // Anrufe und Routen als „Kontakt“ zählen (nur wenn Pixel aktiv)
      var l = ev.target.closest("a[href]");
      if (l && loaded && window.fbq) {
        var h = l.getAttribute("href");
        if (h.indexOf("tel:") === 0) window.fbq("track", "Contact");
        else if (h.indexOf("google.com/maps") > -1) window.fbq("track", "FindLocation");
      }
    });
  }
})();
