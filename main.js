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
})();
