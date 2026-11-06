/* Weihnachts-Intro: hängende 3D-Weihnachtskugeln beim Öffnen der Startseite.
   Ohne fremde Bibliothek (Canvas). Läuft nur einmal pro Besuch, nicht bei
   „Bewegung reduzieren“, und lässt sich jederzeit überspringen.
   Das Overlay selbst wird schon vom Inline-Skript am Seitenanfang angelegt. */
(function () {
  var box = document.getElementById("xm");
  if (!box) return;
  var cv = box.querySelector("canvas"), ctx = cv.getContext("2d");
  if (!ctx) return;
  var W = 0, H = 0, U = 0, DPR = 1;

  // Farben im Stil der Website: Gold, Weinrot, Tannengrün, Champagner
  var PAL = {
    gold:  ["#ffe7b0", "#c9903f", "#5a3612"],
    wine:  ["#ff9c86", "#93302a", "#2e0907"],
    green: ["#8fd1a6", "#1f5a43", "#06180f"],
    champ: ["#fff6e6", "#d8c2a0", "#6d5638"]
  };
  // x: Position (Anteil der Breite), l: Schnurlänge (Anteil der Höhe), r: Größe, z: Tiefe (1 = vorne)
  var BALLS = [
    { x: .10, l: .30, r: .085, z: .55, c: "wine",  d: 120 },
    { x: .22, l: .17, r: .12,  z: 1.0, c: "gold",  d: 0 },
    { x: .36, l: .33, r: .07,  z: .35, c: "green", d: 300 },
    { x: .50, l: .14, r: .095, z: .7,  c: "champ", d: 200 },
    { x: .64, l: .31, r: .075, z: .4,  c: "gold",  d: 380 },
    { x: .78, l: .19, r: .125, z: .95, c: "wine",  d: 60 },
    { x: .91, l: .34, r: .08,  z: .5,  c: "green", d: 260 }
  ];
  BALLS.forEach(function (b, i) { b.ph = i * 1.7; b.spin = (i % 2 ? 1 : -1) * (0.5 + (i % 3) * 0.18); });
  BALLS.sort(function (a, b) { return a.z - b.z; }); // hinten zuerst zeichnen

  var FLAKES = [];
  for (var i = 0; i < 70; i++) FLAKES.push({ x: Math.random(), y: Math.random(), s: .3 + Math.random() * .9, v: .02 + Math.random() * .05, w: Math.random() * 6 });

  function size() {
    DPR = Math.min(window.devicePixelRatio || 1, 2);
    W = box.clientWidth; H = box.clientHeight;
    cv.width = W * DPR; cv.height = H * DPR;
    ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
    U = Math.min(W, H * 0.9);
  }
  size();
  window.addEventListener("resize", size);

  function easeOutBack(t) { var c = 1.4; t -= 1; return 1 + (c + 1) * t * t * t + c * t * t; }
  function easeInCubic(t) { return t * t * t; }
  function clamp(v) { return v < 0 ? 0 : v > 1 ? 1 : v; }

  function ball(b, now, exitT) {
    var col = PAL[b.c], depth = .55 + .45 * b.z;
    var R = b.r * U * depth, ax = b.x * W, len = b.l * H + R * 0.4;
    var mobile = W < 640;
    if (mobile) { len = b.l * H * 0.85 + R * 0.4; }
    var t = (now - b.d) / 1000;
    if (t < 0) return;
    var drop = easeOutBack(clamp(t / 1.0));
    var lift = exitT > 0 ? easeInCubic(clamp(exitT / 0.75)) : 0;
    var oy = -(len + R * 2.4) * (1 - drop) - (len + R * 3) * lift;
    var swing = 0.22 * Math.exp(-t * 0.9) * Math.sin(t * 3.1 + b.ph) + 0.035 * Math.sin(t * 1.3 + b.ph);
    var spin = t * b.spin + b.ph;

    ctx.save();
    ctx.globalAlpha = .55 + .45 * b.z;
    ctx.translate(ax, oy);
    ctx.rotate(swing);
    // Schnur
    ctx.strokeStyle = "rgba(205,185,156,.55)";
    ctx.lineWidth = Math.max(.6, 1.1 * depth);
    ctx.beginPath(); ctx.moveTo(0, -20); ctx.lineTo(0, len - R * 1.02); ctx.stroke();
    ctx.translate(0, len);

    // Kappe
    var cw = R * .38, ch = R * .24;
    var cg = ctx.createLinearGradient(-cw / 2, 0, cw / 2, 0);
    cg.addColorStop(0, "#5b4220"); cg.addColorStop(.45, "#f3d79a"); cg.addColorStop(1, "#6b4d22");
    ctx.fillStyle = cg;
    roundRect(-cw / 2, -R - ch * .75, cw, ch, ch * .25); ctx.fill();
    ctx.strokeStyle = "#d6b36f"; ctx.lineWidth = Math.max(.8, R * .035);
    ctx.beginPath(); ctx.arc(0, -R - ch * .95, R * .07, 0, Math.PI * 2); ctx.stroke();

    // Kugel: Grundfarbe mit Licht von links oben
    var g = ctx.createRadialGradient(-R * .38, -R * .42, R * .05, 0, 0, R);
    g.addColorStop(0, col[0]); g.addColorStop(.45, col[1]); g.addColorStop(1, col[2]);
    ctx.fillStyle = g;
    ctx.beginPath(); ctx.arc(0, 0, R, 0, Math.PI * 2); ctx.fill();

    ctx.save();
    ctx.beginPath(); ctx.arc(0, 0, R, 0, Math.PI * 2); ctx.clip();
    // Drehende Längsstreifen (echte 3D-Projektion)
    ctx.lineWidth = Math.max(.7, R * .028);
    for (var k = 0; k < 6; k++) {
      var p = spin + k * Math.PI / 3, front = Math.cos(p);
      if (front <= 0) continue;
      ctx.strokeStyle = "rgba(255,236,200," + (.32 * front) + ")";
      var rx = Math.abs(Math.sin(p)) * R, side = Math.sin(p) >= 0 ? 1 : -1;
      ctx.beginPath(); ctx.ellipse(0, 0, Math.max(rx, .01), R, 0, -Math.PI / 2, Math.PI / 2, side < 0);
      ctx.stroke();
    }
    // Glitzerband am Äquator
    var ry = R * .2;
    ctx.strokeStyle = "rgba(255,228,170,.55)"; ctx.lineWidth = Math.max(1, R * .07);
    ctx.beginPath(); ctx.ellipse(0, R * .02, R, ry, 0, 0, Math.PI); ctx.stroke();
    for (var j = 0; j < 14; j++) {
      var q = spin * 1.0 + j * Math.PI * 2 / 14, f = Math.cos(q);
      if (f <= 0) continue;
      var dx = Math.sin(q) * R * .98, dy = R * .02 + f * ry;
      ctx.fillStyle = "rgba(255,248,225," + (.35 + .6 * f) + ")";
      ctx.beginPath(); ctx.arc(dx, dy, Math.max(.6, R * .045 * f), 0, Math.PI * 2); ctx.fill();
    }
    // Randschatten
    var rim = ctx.createRadialGradient(0, 0, R * .7, 0, 0, R);
    rim.addColorStop(0, "rgba(0,0,0,0)"); rim.addColorStop(1, "rgba(0,0,0,.45)");
    ctx.fillStyle = rim; ctx.fillRect(-R, -R, R * 2, R * 2);
    // Warmes Gegenlicht unten rechts
    var bl = ctx.createRadialGradient(R * .55, R * .6, 0, R * .55, R * .6, R * .7);
    bl.addColorStop(0, "rgba(255,190,110,.35)"); bl.addColorStop(1, "rgba(255,190,110,0)");
    ctx.fillStyle = bl; ctx.fillRect(-R, -R, R * 2, R * 2);
    ctx.restore();

    // Glanzpunkt
    var hl = ctx.createRadialGradient(-R * .36, -R * .42, 0, -R * .36, -R * .42, R * .34);
    hl.addColorStop(0, "rgba(255,255,255,.95)"); hl.addColorStop(.35, "rgba(255,255,255,.35)"); hl.addColorStop(1, "rgba(255,255,255,0)");
    ctx.fillStyle = hl;
    ctx.beginPath(); ctx.arc(-R * .36, -R * .42, R * .34, 0, Math.PI * 2); ctx.fill();
    ctx.restore();
  }

  function roundRect(x, y, w, h, r) {
    ctx.beginPath(); ctx.moveTo(x + r, y); ctx.lineTo(x + w - r, y); ctx.quadraticCurveTo(x + w, y, x + w, y + r);
    ctx.lineTo(x + w, y + h - r); ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h); ctx.lineTo(x + r, y + h);
    ctx.quadraticCurveTo(x, y + h, x, y + h - r); ctx.lineTo(x, y + r); ctx.quadraticCurveTo(x, y, x + r, y); ctx.closePath();
  }

  function snow(dt) {
    for (var i = 0; i < FLAKES.length; i++) {
      var f = FLAKES[i];
      f.y += f.v * dt; if (f.y > 1.05) { f.y = -.05; f.x = Math.random(); }
      var x = (f.x + Math.sin(f.y * 6 + f.w) * .012) * W, y = f.y * H;
      ctx.fillStyle = "rgba(242,220,170," + (.25 + .35 * f.s) + ")";
      ctx.beginPath(); ctx.arc(x, y, (1 + f.s * 1.8) * (W < 640 ? .8 : 1), 0, Math.PI * 2); ctx.fill();
    }
  }

  var start = performance.now(), last = start, exitAt = 0, done = false, HOLD = 3600;
  function frame(ts) {
    if (done) return;
    var now = ts - start, dt = Math.min(.05, (ts - last) / 1000); last = ts;
    if (!exitAt && now > HOLD) leave();
    var exitT = exitAt ? (ts - exitAt) / 1000 : 0;
    ctx.clearRect(0, 0, W, H);
    snow(dt);
    for (var i = 0; i < BALLS.length; i++) ball(BALLS[i], now, exitT);
    requestAnimationFrame(frame);
  }
  function leave() {
    if (exitAt) return;
    exitAt = performance.now();
    box.classList.add("xm-out");
    setTimeout(finish, 850);
  }
  function finish() {
    done = true;
    if (window.__xmFinish) window.__xmFinish();
  }
  box.addEventListener("click", leave);
  document.addEventListener("keydown", function (e) { if (e.key === "Escape" || e.key === "Enter" || e.key === " ") leave(); });
  box.classList.add("xm-run");
  requestAnimationFrame(frame);
})();
