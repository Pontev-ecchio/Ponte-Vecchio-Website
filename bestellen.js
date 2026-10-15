/* Bestellen (Abholung) und Reservieren (Tisch, optional mit Essen) per WhatsApp.
   Die Daten (Speisekarte, Öffnungszeiten, Einstellungen) kommen aus build.py
   über <script id="order-data">. Alles läuft im Browser, es wird nichts gespeichert
   außer der Tischauswahl beim Wechsel von /reservieren/ zu /bestellen/ (sessionStorage). */
(function () {
  var dataEl = document.getElementById("order-data");
  if (!dataEl) return;
  var D = JSON.parse(dataEl.textContent), S = D.settings;
  var PAGE = document.body.getAttribute("data-page"); // "bestellen" | "reservieren"
  var KEY = "pv-tisch-v1";

  /* ---------- Hilfsfunktionen ---------- */
  var $ = function (id) { return document.getElementById(id); };
  var esc = function (s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); };
  var fmt = function (n) { return n.toFixed(2).replace(".", ",") + " €"; };
  var pad = function (n) { return String(n).padStart(2, "0"); };
  var hhmm = function (m) { return pad(Math.floor(m / 60)) + ":" + pad(m % 60); };
  var store = {
    get: function () { try { return JSON.parse(sessionStorage.getItem(KEY) || "null"); } catch (e) { return null; } },
    set: function (v) { try { sessionStorage.setItem(KEY, JSON.stringify(v)); return true; } catch (e) { return false; } },
    del: function () { try { sessionStorage.removeItem(KEY); } catch (e) {} }
  };

  /* ---------- Uhrzeiten (immer Regensburger Zeit) ---------- */
  function berlinNow() {
    var p = new Intl.DateTimeFormat("en-CA", { timeZone: "Europe/Berlin", year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", hourCycle: "h23" }).formatToParts(new Date());
    var g = function (t) { return parseInt(p.find(function (x) { return x.type === t; }).value, 10); };
    return { y: g("year"), m: g("month"), d: g("day"), min: g("hour") * 60 + g("minute") };
  }
  // Ein Tag (offset 0 = heute) mit allen wählbaren Uhrzeiten, getrennt nach Öffnungszeit-Blöcken
  function dayInfo(offset) {
    var n = berlinNow();
    var dt = new Date(Date.UTC(n.y, n.m - 1, n.d + offset));
    var wd = (dt.getUTCDay() + 6) % 7; // 0 = Montag
    var min = offset === 0 ? n.min + S.lead : -1;
    var groups = (S.hours[wd] || []).map(function (r) {
      var s = [];
      for (var t = r[0]; t <= r[1] - S.last; t += S.step) if (t >= min) s.push(hhmm(t));
      return s;
    });
    var label = offset === 0 ? "Heute" : offset === 1 ? "Morgen" : S.days[wd];
    return { offset: offset, iso: dt.toISOString().slice(0, 10), wd: wd, label: label,
      date: pad(dt.getUTCDate()) + "." + pad(dt.getUTCMonth() + 1) + ".", dnum: dt.getUTCDate(),
      mon: dt.toLocaleDateString("de-DE", { month: "short", timeZone: "UTC" }), groups: groups,
      has: groups.some(function (g) { return g.length; }) };
  }
  function openDays(max) { var out = []; for (var i = 0; i < max; i++) { var d = dayInfo(i); if (d.has) out.push(d); } return out; }
  function nextOpenDay() { for (var i = 0; i < 8; i++) { var d = dayInfo(i); if (d.has) return d; } return null; }
  function longDay(d) { return d.label + (d.offset < 2 ? ", " + S.days[d.wd] : "") + ", " + d.date; }
  function slotStillValid(iso, time) {
    for (var i = 0; i < S.resDays; i++) { var d = dayInfo(i); if (d.iso === iso) return d.groups.some(function (g) { return g.indexOf(time) > -1; }); }
    return false;
  }
  function findDay(iso) { for (var i = 0; i < S.resDays; i++) { var d = dayInfo(i); if (d.iso === iso) return d; } return null; }

  function slotButtons(groups, sel, attr) {
    return groups.map(function (g, gi) {
      if (!g.length) return "";
      var lbl = groups.length > 1 ? (gi ? "Abends" : "Mittags") : "";
      return (lbl ? '<p class="o-sub">' + lbl + "</p>" : "") + '<div class="o-opts">' + g.map(function (t) {
        return '<button type="button" class="o-opt o-num" ' + attr + '="' + t + '" aria-pressed="' + (sel === t) + '">' + t + "</button>";
      }).join("") + "</div>";
    }).join("");
  }
  var WA_ICON = '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2Zm0 18.2a8.2 8.2 0 0 1-4.2-1.2l-.3-.2-3 .8.8-2.9-.2-.3A8.2 8.2 0 1 1 12 20.2Zm4.5-6.1c-.2-.1-1.5-.7-1.7-.8s-.4-.1-.6.1-.7.8-.8 1-.3.2-.5.1a6.7 6.7 0 0 1-3.3-2.9c-.3-.4.3-.4.7-1.3.1-.2 0-.3 0-.4l-.8-1.8c-.2-.5-.4-.4-.6-.4h-.5a1 1 0 0 0-.7.3 3 3 0 0 0-.9 2.2 5.1 5.1 0 0 0 1.1 2.7 11.6 11.6 0 0 0 4.5 4c1.7.7 2.3.8 3.2.6a2.7 2.7 0 0 0 1.8-1.2 2.2 2.2 0 0 0 .1-1.3c0-.1-.2-.2-.4-.3Z"/></svg>';
  var waUrl = function (text) { return "https://wa.me/" + S.wa + "?text=" + encodeURIComponent(text); };
  var personsTxt = function (p) { return p + " " + (p === 1 ? "Person" : "Personen"); };
  var kidsTxt = function (k) { return k + " Kinderstuhl" + (k > 1 ? "e" : ""); };

  if (PAGE === "reservieren") reservePage(); else orderPage();

  /* =====================================================================
     RESERVIEREN
     ===================================================================== */
  function reservePage() {
    var st = { day: null, time: "", persons: 2, kids: 0, food: "no" };
    var prev = store.get();
    if (prev) { st.day = prev.iso; st.time = prev.time; st.persons = prev.persons; st.kids = prev.kids; st.food = "yes";
      $("r-name").value = prev.name || ""; $("r-note").value = prev.note || ""; }

    function render() {
      var list = openDays(S.resDays);
      if (!list.some(function (d) { return d.iso === st.day; })) st.day = list[0] ? list[0].iso : null;
      $("r-days").innerHTML = list.map(function (d) {
        return '<button type="button" class="o-day" data-day="' + d.iso + '" aria-pressed="' + (d.iso === st.day) + '"><small>' +
          (d.offset < 2 ? d.label : S.days[d.wd].slice(0, 2)) + "</small><b>" + d.dnum + "</b><span>" + esc(d.mon) + "</span></button>";
      }).join("");
      var cur = list.find(function (d) { return d.iso === st.day; });
      if (!cur || !cur.groups.some(function (g) { return g.indexOf(st.time) > -1; })) st.time = "";
      $("r-times").innerHTML = cur ? slotButtons(cur.groups, st.time, "data-time") : '<p class="o-muted">Zurzeit sind keine Reservierungen möglich.</p>';
      var ps = []; for (var i = 1; i <= S.maxP; i++) ps.push(i);
      $("r-persons").innerHTML = ps.map(function (n) { return '<button type="button" class="o-opt o-num" data-p="' + n + '" aria-pressed="' + (st.persons === n) + '">' + n + "</button>"; }).join("");
      $("r-kids").innerHTML = [0, 1, 2, 3].map(function (n) { return '<button type="button" class="o-opt" data-k="' + n + '" aria-pressed="' + (st.kids === n) + '">' + (n ? kidsTxt(n) : "Keiner") + "</button>"; }).join("");
      $("r-food").innerHTML = [["no", "Nein, nur Tisch"], ["yes", "Ja, Essen auswählen"]].map(function (o) {
        return '<button type="button" class="o-opt" data-food="' + o[0] + '" aria-pressed="' + (st.food === o[0]) + '">' + o[1] + "</button>"; }).join("");
      summary();
    }
    function curDay() { return findDay(st.day); }
    function whenTxt() { var d = curDay(); return d ? longDay(d) + (st.time ? ", " + st.time + " Uhr" : "") : ""; }
    function summary() {
      $("r-sum").innerHTML = "Tisch für <em>" + personsTxt(st.persons) + "</em>" + (st.kids ? " · " + kidsTxt(st.kids) : "") +
        "<br>" + esc(whenTxt()) + (st.time ? "" : ' <span class="o-muted">· Uhrzeit wählen</span>');
      var btn = $("r-send");
      if (st.food === "yes") {
        btn.className = "btn btn-gold o-send"; btn.removeAttribute("target");
        btn.innerHTML = "Weiter zur Essensauswahl"; btn.href = "/bestellen/?tisch=1";
        $("r-hint").hidden = true;
      } else {
        btn.className = "o-wa o-send"; btn.target = "_blank"; btn.rel = "noopener";
        btn.innerHTML = WA_ICON + "Per WhatsApp reservieren";
        var name = $("r-name").value.trim(), note = $("r-note").value.trim();
        btn.href = waUrl(["Hallo Ponte Vecchio, ich möchte einen Tisch reservieren:", "",
          "Tag: " + whenTxt(), "Personen: " + st.persons].concat(st.kids ? ["Kinderstuhl: " + st.kids] : [])
          .concat(["Name: " + name]).concat(note ? ["Anmerkung: " + note] : []).concat(["", "Bitte um kurze Bestätigung. Danke!"]).join("\n"));
        $("r-hint").hidden = false;
      }
    }
    function validate() {
      var m = "";
      if (!st.time) m = "Bitte wählen Sie eine Uhrzeit.";
      else if (!$("r-name").value.trim()) m = "Bitte geben Sie Ihren Namen ein.";
      $("r-err").textContent = m; $("r-err").hidden = !m; return !m;
    }
    document.addEventListener("click", function (e) {
      var t = e.target.closest("button, a"); if (!t) return; var d = t.dataset;
      if (d.day) { st.day = d.day; st.time = ""; render(); focusSel('[data-day="' + d.day + '"]'); }
      else if (d.time) { st.time = d.time; render(); focusSel('[data-time="' + d.time + '"]'); }
      else if (d.p) { st.persons = +d.p; render(); focusSel('[data-p="' + d.p + '"]'); }
      else if (d.k) { st.kids = +d.k; render(); focusSel('[data-k="' + d.k + '"]'); }
      else if (d.food) { st.food = d.food; render(); focusSel('[data-food="' + d.food + '"]'); }
      else if (t.id === "r-send") {
        summary();
        if (!validate()) { e.preventDefault(); return; }
        if (st.food === "yes") {
          var res = { iso: st.day, time: st.time, persons: st.persons, kids: st.kids, name: $("r-name").value.trim(), note: $("r-note").value.trim() };
          if (!store.set(res)) t.href = "/bestellen/?tisch=" + encodeURIComponent([res.iso, res.time, res.persons, res.kids].join("_"));
        } else store.del();
      }
      if (t.id !== "r-send" && !$("r-err").hidden) validate();
    });
    document.addEventListener("input", function () { summary(); if (!$("r-err").hidden) validate(); });
    setInterval(function () { var had = st.time; render(); if (had && !st.time) validate(); }, 60000);
    render();
  }

  /* =====================================================================
     BESTELLEN (Abholung oder Essen zur Tischreservierung)
     ===================================================================== */
  function orderPage() {
    var ITEMS = {};
    D.menu.forEach(function (c) { c.items.forEach(function (it, i) { it.id = c.id + "-" + i; ITEMS[it.id] = it; }); });
    var cart = [];
    var form = { name: "", slot: "", note: "" };

    // Tisch-Modus: Reservierung aus /reservieren/ übernehmen
    var table = null, q = new URLSearchParams(location.search).get("tisch");
    if (q) {
      table = store.get();
      if (!table && q.indexOf("_") > -1) { var a = q.split("_"); table = { iso: a[0], time: a[1], persons: +a[2], kids: +a[3], name: "", note: "" }; }
      if (table) { form.name = table.name || ""; form.note = table.note || ""; }
    }
    var plan = nextOpenDay();

    if (table) {
      document.title = "Essen vorbestellen | Ponte Vecchio Regensburg";
      $("o-title").textContent = "Essen vorbestellen";
      $("o-lead").textContent = "Wählen Sie Ihr Essen für Ihre Reservierung. Wir bereiten alles zu Ihrer Ankunftszeit vor.";
      var d = findDay(table.iso);
      $("o-table").hidden = false;
      $("o-table-txt").innerHTML = "Tisch für <em>" + personsTxt(table.persons) + "</em>" + (table.kids ? " · " + kidsTxt(table.kids) : "") +
        "<br>" + esc(d ? longDay(d) : table.iso) + ", " + esc(table.time) + " Uhr";
    }

    /* Speisekarte */
    function itemHTML(it) {
      var inCart = cart.filter(function (l) { return l.id === it.id; }).reduce(function (s, l) { return s + l.qty; }, 0);
      var ctl = (!it.groups.length && inCart)
        ? '<div class="o-step"><button type="button" data-dec="' + it.id + '" aria-label="' + esc(it.n) + ' weniger">−</button><span>' + inCart + '</span><button type="button" data-add="' + it.id + '" aria-label="' + esc(it.n) + ' mehr">+</button></div>'
        : '<button type="button" class="o-add" data-add="' + it.id + '" aria-label="' + esc(it.n) + ' hinzufügen">+</button>';
      return '<li class="dish o-dish" id="row-' + it.id + '"><div class="o-txt"><div class="dish-h"><h3>' + esc(it.n) +
        '</h3><span class="lead" aria-hidden="true"></span><span class="price">' + fmt(it.p) + "</span></div>" +
        (it.d ? '<p class="dish-d">' + esc(it.d) + "</p>" : "") +
        (it.groups.length && inCart ? '<span class="o-badge">' + inCart + " im Warenkorb</span>" : "") + "</div>" + ctl + "</li>";
    }
    $("o-chips").innerHTML = D.menu.map(function (c) { return '<a href="#' + c.id + '">' + esc(c.name) + "</a>"; }).join("");
    $("o-menu").innerHTML = D.menu.map(function (c) {
      var extra = c.extras ? '<div class="extras"><h3>Extrazutaten</h3><ul>' + c.extras.map(function (x) {
        return '<li><span class="price">je ' + esc(x.preis) + "</span><span>" + esc(x.zutaten) + "</span></li>"; }).join("") +
        '</ul><p class="o-muted o-small">Auswählbar nach Tippen auf + bei jeder Pizza.</p></div>' : "";
      return '<section class="cat" id="' + c.id + '"><h2>' + esc(c.name) + "</h2>" + (c.note ? '<p class="cat-note">' + esc(c.note) + "</p>" : "") +
        '<ul class="dishes">' + c.items.map(itemHTML).join("") + "</ul>" + extra + "</section>";
    }).join("");
    function refreshRow(id) { var r = $("row-" + id); if (r) r.outerHTML = itemHTML(ITEMS[id]); }

    /* Warenkorb */
    function addLine(line) {
      var ex = cart.find(function (l) { return l.key === line.key; });
      if (ex) ex.qty += line.qty; else cart.push(line);
      update(line.id);
    }
    function update(id) {
      if (id) refreshRow(id);
      var n = cart.reduce(function (s, l) { return s + l.qty; }, 0), sum = cart.reduce(function (s, l) { return s + l.qty * l.unit; }, 0);
      var bb = $("o-open");
      bb.classList.toggle("o-empty", n === 0);
      $("o-cnt").textContent = n; $("o-sum").textContent = fmt(sum);
      $("o-barlbl").textContent = n ? (table ? "Weiter: Bestellung senden" : "Warenkorb & WhatsApp") : "Noch nichts ausgewählt";
      if (!$("o-cart").hidden) renderCart();
    }

    /* Auswahl-Fenster (Extras, Nudeln, Sorte …) */
    var cur = null;
    function openOptions(it) { cur = { it: it, sel: it.groups.map(function (g) { return g.type === "one" ? null : []; }), qty: 1 }; renderOptions(); show("o-opt"); }
    function optPrice() {
      var p = cur.it.p;
      cur.it.groups.forEach(function (g, gi) {
        if (g.type === "one") { if (cur.sel[gi] != null) p += g.choices[cur.sel[gi]].p || 0; }
        else cur.sel[gi].forEach(function (ci) { p += g.choices[ci].p || 0; });
      });
      return p;
    }
    function renderOptions() {
      var it = cur.it;
      var missing = it.groups.filter(function (g, gi) { return g.type === "one" && cur.sel[gi] == null; }).map(function (g) { return g.label; });
      $("o-optbox").innerHTML = '<div class="o-sh"><div><h2 id="o-opt-t">' + esc((it.prefix ? it.prefix + " " : "") + it.n) + "</h2>" +
        (it.d ? '<p class="dish-d">' + esc(it.d) + "</p>" : "") + '</div><button type="button" class="o-x" data-close="o-opt" aria-label="Schließen">×</button></div>' +
        it.groups.map(function (g, gi) {
          return '<div class="o-grp"><h3>' + esc(g.label) + " <i>· " + esc(g.hint || (g.type === "one" ? "bitte wählen" : "optional, mehrere möglich")) + '</i></h3><div class="o-opts">' +
            g.choices.map(function (c, ci) {
              var on = g.type === "one" ? cur.sel[gi] === ci : cur.sel[gi].indexOf(ci) > -1;
              return '<button type="button" class="o-opt" aria-pressed="' + on + '" data-g="' + gi + '" data-c="' + ci + '">' + esc(c.n) + (c.p ? "<small>+" + fmt(c.p) + "</small>" : "") + "</button>";
            }).join("") + "</div></div>";
        }).join("") +
        '<div class="o-sf"><div class="o-step"><button type="button" data-oq="-1" aria-label="weniger">−</button><span>' + cur.qty + '</span><button type="button" data-oq="1" aria-label="mehr">+</button></div>' +
        '<button type="button" class="btn btn-gold o-grow" id="o-optadd"' + (missing.length ? " disabled" : "") + ">" +
        (missing.length ? "Bitte " + esc(missing[0]) + " wählen" : "Hinzufügen · " + fmt(optPrice() * cur.qty)) + "</button></div>";
    }
    function commitOptions() {
      var it = cur.it, parts = [], nameChoice = null;
      it.groups.forEach(function (g, gi) {
        if (g.type === "one") { var c = g.choices[cur.sel[gi]].n; if (it.useChoice && nameChoice === null) nameChoice = c; else parts.push(c); }
        else { var ex = cur.sel[gi].slice().sort(function (a, b) { return a - b; }).map(function (ci) { return g.choices[ci].n; });
          if (ex.length) parts.push(g.plain ? ex.join(", ") : "+ " + ex.join(", + ")); }
      });
      if (it.size) parts.unshift(it.size);
      var label = nameChoice !== null ? nameChoice : (it.prefix ? it.prefix + " " : "") + it.n, detail = parts.join(" · ");
      addLine({ key: it.id + "|" + label + "|" + detail, id: it.id, label: label, detail: detail, unit: optPrice(), qty: cur.qty });
      hide("o-opt");
    }

    /* Warenkorb-Fenster */
    function whenTxt() {
      if (table) { var d = findDay(table.iso); return (d ? longDay(d) : table.iso) + ", " + table.time + " Uhr"; }
      if (!plan || !form.slot) return "";
      return (plan.offset === 0 ? "heute" : plan.offset === 1 ? "morgen, " + plan.date : S.days[plan.wd] + ", " + plan.date) + " um " + form.slot + " Uhr";
    }
    function message() {
      var sum = cart.reduce(function (s, l) { return s + l.qty * l.unit; }, 0);
      var lines = cart.map(function (l) { return l.qty + "x " + l.label + (l.detail ? " (" + l.detail + ")" : "") + " – " + fmt(l.qty * l.unit); });
      var head = table
        ? ["Hallo Ponte Vecchio, ich möchte einen Tisch reservieren und das Essen vorbestellen:", "",
           "Tag: " + whenTxt(), "Personen: " + table.persons].concat(table.kids ? ["Kinderstuhl: " + table.kids] : []).concat(["Name: " + form.name.trim(), "", "Essen:"])
        : ["Hallo Ponte Vecchio, ich möchte zur Abholung bestellen:", ""];
      var tail = table ? ["", "Summe: " + fmt(sum), "Bezahlung: vor Ort"]
        : ["", "Summe: " + fmt(sum), "Name: " + form.name.trim(), "Abholung: " + whenTxt(), "Bezahlung: vor Ort"];
      return head.concat(lines, tail, form.note.trim() ? ["Anmerkung: " + form.note.trim()] : []).join("\n");
    }
    function renderCart() {
      var el = $("o-cartbox"), sum = cart.reduce(function (s, l) { return s + l.qty * l.unit; }, 0);
      var top = '<div class="o-sh"><h2 id="o-cart-t">Ihre Bestellung</h2><button type="button" class="o-x" data-close="o-cart" aria-label="Schließen">×</button></div>';
      if (!cart.length) { el.innerHTML = top + '<p class="o-muted">Der Warenkorb ist leer.</p>'; return; }
      var when = table
        ? '<div class="o-grp"><h3>Ihre Reservierung</h3><p class="o-res">Tisch für ' + personsTxt(table.persons) + (table.kids ? " · " + kidsTxt(table.kids) : "") + "<br>" + esc(whenTxt()) +
          '</p><a class="o-link" href="/reservieren/">Reservierung ändern</a></div>'
        : '<div class="o-grp"><h3>Abholzeit <i>· frühestens ' + S.lead + " Minuten nach Bestellung</i></h3>" +
          (plan ? '<p class="o-day-t">' + esc(plan.offset === 0 ? "Heute" : longDay(plan)) + "</p>" + slotButtons(plan.groups, form.slot, "data-slot")
            : '<p class="o-muted">Zurzeit ist keine Abholung möglich.</p>') + "</div>";
      el.innerHTML = top +
        '<ul class="o-lines">' + cart.map(function (l, i) {
          return '<li class="o-line"><div class="o-txt"><p class="o-ln">' + esc(l.label) + "</p>" + (l.detail ? '<p class="dish-d">' + esc(l.detail) + "</p>" : "") +
            '<p class="o-lp">' + l.qty + " × " + fmt(l.unit) + '</p></div><div class="o-step"><button type="button" data-ld="' + i + '" aria-label="weniger">−</button><span>' + l.qty +
            '</span><button type="button" data-li="' + i + '" aria-label="mehr">+</button></div></li>';
        }).join("") + "</ul>" +
        '<div class="o-tot"><span>Summe</span><b>' + fmt(sum) + "</b></div>" +
        '<div class="o-fld"><label for="f-name">Ihr Name</label><input id="f-name" autocomplete="name" value="' + esc(form.name) + '" placeholder="z. B. Maria Huber"></div>' +
        when +
        '<div class="o-fld"><label for="f-note">Anmerkung (optional)</label><textarea id="f-note" placeholder="z. B. Pizza gut durch, ohne Zwiebeln">' + esc(form.note) + "</textarea></div>" +
        '<p class="o-err" id="o-err" hidden></p>' +
        '<a class="o-wa" id="o-wa" href="#" target="_blank" rel="noopener">' + WA_ICON + "Per WhatsApp " + (table ? "senden" : "bestellen") + " · " + fmt(sum) + "</a>" +
        '<p class="o-hint">WhatsApp öffnet sich mit Ihrer fertigen Bestellung an ' + esc(S.waText) + ". Sie müssen nur noch auf Senden tippen. Bezahlung vor Ort, bar oder mit Karte.</p>" +
        '<p class="o-hint">Bitte warten Sie auf unsere Antwort im Chat. Falls innerhalb von 5 Minuten keine Antwort kommt, rufen Sie uns bitte an: ' + esc(S.waText) + ".</p>";
      syncWa();
    }
    function syncWa() { var a = $("o-wa"); if (a) a.href = waUrl(message()); }
    function validate() {
      var m = "";
      if (!form.name.trim()) m = "Bitte geben Sie Ihren Namen ein, damit wir die Bestellung zuordnen können.";
      else if (table && !slotStillValid(table.iso, table.time)) m = "Die gewählte Uhrzeit ist nicht mehr möglich. Bitte ändern Sie die Reservierung.";
      else if (!table && !form.slot) m = "Bitte wählen Sie eine Abholzeit.";
      var e = $("o-err"); e.textContent = m; e.hidden = !m; return !m;
    }

    /* Ereignisse */
    document.addEventListener("click", function (e) {
      var t = e.target.closest("button, a, .o-scrim"); if (!t) return; var d = t.dataset;
      if (t.classList.contains("o-scrim")) { if (e.target === t) hide(t.id); return; }
      if (d.add) { var it = ITEMS[d.add]; if (it.groups.length) openOptions(it); else addLine({ key: it.id, id: it.id, label: (it.prefix ? it.prefix + " " : "") + it.n, detail: /^\d/.test(it.d) ? it.d : "", unit: it.p, qty: 1 }); return; }
      if (d.dec) { var l = cart.find(function (x) { return x.key === d.dec; }); if (l) { l.qty--; if (!l.qty) cart.splice(cart.indexOf(l), 1); } update(d.dec); return; }
      if (d.close) { hide(d.close); return; }
      if (d.g !== undefined) { var gi = +d.g, ci = +d.c, g = cur.it.groups[gi];
        if (g.type === "one") cur.sel[gi] = ci; else { var k = cur.sel[gi].indexOf(ci); if (k > -1) cur.sel[gi].splice(k, 1); else cur.sel[gi].push(ci); }
        renderOptions(); focusSel('[data-g="' + gi + '"][data-c="' + ci + '"]'); return; }
      if (d.oq) { cur.qty = Math.max(1, cur.qty + (+d.oq)); renderOptions(); return; }
      if (t.id === "o-optadd") { commitOptions(); return; }
      if (t.id === "o-open") { if (!cart.length) { $("o-menu").scrollIntoView({ behavior: "smooth" }); return; } refreshPlan(); renderCart(); show("o-cart"); return; }
      if (d.li !== undefined) { cart[+d.li].qty++; update(cart[+d.li].id); return; }
      if (d.ld !== undefined) { var ln = cart[+d.ld]; ln.qty--; if (!ln.qty) cart.splice(+d.ld, 1); update(ln.id); if (!cart.length) hide("o-cart"); return; }
      if (d.slot) { form.slot = d.slot; renderCart(); focusSel('[data-slot="' + d.slot + '"]'); return; }
      if (t.id === "o-wa") { syncWa(); if (!validate()) e.preventDefault(); return; }
    });
    document.addEventListener("input", function (e) {
      if (e.target.id === "f-name") form.name = e.target.value;
      else if (e.target.id === "f-note") form.note = e.target.value;
      else return;
      syncWa(); var er = $("o-err"); if (er && !er.hidden) validate();
    });
    function refreshPlan() {
      var np = nextOpenDay(), sig = function (p) { return p ? p.iso + p.groups.join("|") : ""; }, changed = sig(np) !== sig(plan);
      plan = np;
      if (form.slot && !(plan && plan.groups.some(function (g) { return g.indexOf(form.slot) > -1; }))) form.slot = "";
      return changed;
    }
    setInterval(function () { if (refreshPlan() && !$("o-cart").hidden) renderCart(); }, 30000);
    update();
  }

  /* ---------- Fenster öffnen/schließen ---------- */
  var lastFocus = null;
  function show(id) { lastFocus = document.activeElement; $(id).hidden = false; document.body.classList.add("o-lock"); var b = document.querySelector("#" + id + " .o-x"); if (b) b.focus(); }
  function hide(id) { $(id).hidden = true; if (!document.querySelector(".o-scrim:not([hidden])")) document.body.classList.remove("o-lock"); if (lastFocus && lastFocus.focus) lastFocus.focus(); }
  function focusSel(sel) { var b = document.querySelector(sel); if (b) b.focus(); }
  document.addEventListener("keydown", function (e) { if (e.key === "Escape") document.querySelectorAll(".o-scrim:not([hidden])").forEach(function (s) { hide(s.id); }); });
})();
