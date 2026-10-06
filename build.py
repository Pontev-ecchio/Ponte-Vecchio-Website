#!/usr/bin/env python3
"""
Baut die Website von Ponte Vecchio.

Die Inhalte liegen in content/*.json und werden über den Admin-Bereich (/admin)
bearbeitet. Bei jeder Änderung baut Netlify die Seite automatisch neu:
    python3 build.py   ->  Ergebnis im Ordner dist/
"""
import html, json, os, re, shutil, urllib.parse, urllib.request
from datetime import date

ROOT = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(ROOT, "dist")
e = html.escape


def find(name, sub):
    """Datei im Unterordner suchen, sonst in der Hauptebene (GitHub-Upload ohne Ordner)."""
    p = os.path.join(ROOT, sub, name)
    return p if os.path.exists(p) else os.path.join(ROOT, name)


def load(name):
    with open(find(name, "content"), encoding="utf-8") as f:
        return json.load(f)


B = load("betrieb.json")
H = load("oeffnungszeiten.json")
M = load("speisekarte.json")
R = load("rechtliches.json")

DOMAIN = B.get("domain", "").rstrip("/")
INDEX = bool(B.get("suchmaschinen_freigeben"))
TEL = "+" + re.sub(r"\D", "", B["telefon"])
ADDR_Q = f'{B["name"]}, {B["strasse"]}, {B["plz"]} {B["ort"]}'
MAPS = "https://www.google.com/maps/search/?api=1&query=" + urllib.parse.quote_plus(ADDR_Q)


def slug(t):
    t = t.lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")


def mins(t):
    h, m = t.strip().split(":")
    return int(h) * 60 + int(m)


# ---------- Bausteine ----------
def head(title, desc, path):
    robots = "index,follow" if INDEX else "noindex,nofollow"
    url = DOMAIN + path
    return f"""<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<meta name="robots" content="{robots}">
<link rel="canonical" href="{e(url)}">
<meta name="theme-color" content="#171614">
<meta property="og:type" content="restaurant">
<meta property="og:locale" content="de_DE">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{e(url)}">
<meta property="og:image" content="{e(DOMAIN)}/img/bar-theke.jpg">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="preload" href="/fonts/cormorant-500.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/style.css">
</head>
<body>
"""


def header(active=""):
    cur = lambda k: ' aria-current="page"' if k == active else ""
    sonder = H.get("sonderhinweis", "").strip()
    banner = f'<p class="sonder" role="status">{e(sonder)}</p>' if sonder else ""
    return f"""<a class="skip" href="#main">Zum Inhalt springen</a>
{banner}
<header class="hdr">
  <div class="wrap">
    <a class="brand" href="/" aria-label="{e(B['name'])} – Startseite">
      <span class="logo"><b>Ponte Vecchio</b><small>Bar · Caffè · Pizzeria</small></span>
    </a>
    <nav class="nav" aria-label="Hauptnavigation">
      <a class="nl" href="/speisekarte/"{cur('menu')}>Speisekarte</a>
      <a class="nl" href="/#bar">Bar &amp; Café</a>
      <a class="nl" href="/#zeiten">Öffnungszeiten</a>
      <a class="nl" href="/#kontakt">Kontakt</a>
      <a class="btn btn-gold" href="tel:{TEL}">Reservieren</a>
    </nav>
  </div>
</header>
<main id="main">
"""


IG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r="1" fill="currentColor" stroke="none"/></svg>'
FB = '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M14 8h3V4h-3c-2.8 0-4.5 1.8-4.5 4.6V11H7v4h2.5v6h4v-6h3l.5-4h-3.5V8.8c0-.5.3-.8.5-.8z"/></svg>'


def social():
    """Nur einfache Links: keine Einbettung, keine Cookies, kein Banner nötig."""
    out = []
    if B.get("instagram", "").strip():
        out.append(f'<a class="soc" href="{e(B["instagram"].strip())}" target="_blank" rel="noopener" aria-label="Ponte Vecchio auf Instagram">{IG}<span>Instagram</span></a>')
    if B.get("facebook", "").strip():
        out.append(f'<a class="soc" href="{e(B["facebook"].strip())}" target="_blank" rel="noopener" aria-label="Ponte Vecchio auf Facebook">{FB}<span>Facebook</span></a>')
    return f'<div class="socials">{"".join(out)}</div>' if out else ""


def footer():
    return f"""</main>
<footer class="ftr">
  <div class="wrap">
    <div>
      <p style="font:600 1.6rem/1.1 var(--f-display);color:var(--cream)">Ponte Vecchio</p>
      <p style="margin-top:.6rem">Bar, Café &amp; Pizzeria im Regensburger Ostenviertel.<br>{e(B['strasse'])}, {e(B['plz'])} {e(B['ort'])}<br>Telefon {e(B['telefon'])}</p>
      {social()}
    </div>
    <div>
      <h3>Seiten</h3>
      <ul><li><a href="/">Startseite</a></li><li><a href="/speisekarte/">Speisekarte</a></li><li><a href="/#zeiten">Öffnungszeiten</a></li><li><a href="/#kontakt">Kontakt</a></li></ul>
    </div>
    <div>
      <h3>Rechtliches</h3>
      <ul><li><a href="/impressum/">Impressum</a></li><li><a href="/datenschutz/">Datenschutz</a></li></ul>
    </div>
    <p class="copy">© {date.today().year} {e(B['name'])}</p>
  </div>
</footer>
<nav class="mbar" aria-label="Schnellaktionen">
  <a href="/speisekarte/"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M5 4h11a3 3 0 0 1 3 3v13H8a3 3 0 0 1-3-3z"/><path d="M9 9h6M9 13h6"/></svg>Speisekarte</a>
  <a href="tel:{TEL}"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2"/></svg>Anrufen</a>
  <a href="{e(MAPS)}" target="_blank" rel="noopener"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M12 21s-7-6.2-7-11.5A7 7 0 0 1 19 9.5C19 14.8 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/></svg>Route</a>
</nav>
<script src="/main.js" defer></script>
</body>
</html>
"""


# ---------- Öffnungszeiten ----------
DAYS_EN = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def hours_rows():
    rows = []
    for i, d in enumerate(H["tage"]):
        z = d.get("zeiten") or []
        txt = " · ".join(f'{x["von"]}–{x["bis"]}' for x in z) if z else "Ruhetag"
        rows.append(f'<tr data-day="{i}"><th scope="row">{e(d["tag"])}</th><td>{e(txt)}</td></tr>')
    return "".join(rows)


def hours_js():
    arr = [[[mins(x["von"]), mins(x["bis"])] for x in (d.get("zeiten") or [])] for d in H["tage"]]
    names = [d["tag"] for d in H["tage"]]
    return json.dumps({"h": arr, "n": names}, ensure_ascii=False)


def schema():
    spec = []
    for i, d in enumerate(H["tage"]):
        for x in d.get("zeiten") or []:
            spec.append({"@type": "OpeningHoursSpecification", "dayOfWeek": DAYS_EN[i], "opens": x["von"], "closes": x["bis"]})
    data = {"@context": "https://schema.org", "@type": "Restaurant", "name": B["name"], "url": DOMAIN + "/",
            "telephone": TEL, "priceRange": B.get("preisniveau", ""), "servesCuisine": ["Italienisch", "Pizza", "Pasta"],
            "acceptsReservations": "True", "hasMenu": DOMAIN + "/speisekarte/", "image": DOMAIN + "/img/bar-theke.jpg",
            "address": {"@type": "PostalAddress", "streetAddress": B["strasse"], "postalCode": B["plz"],
                        "addressLocality": B["ort"], "addressCountry": "DE"},
            "openingHoursSpecification": spec}
    return '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False) + "</script>"


# ---------- Seiten ----------
def page_home():
    t = open(os.path.join(ROOT, "templates_home.html"), encoding="utf-8").read()
    bar = "".join(f'<li><span>{e(x["name"])}</span><span class="lead"></span><span class="p">{e(x["preis"])}</span></li>'
                  for x in B.get("bar_auswahl", []))
    addr = f'<strong>{e(B["name"])}</strong>{e(B["strasse"])}<br>{e(B["plz"])} {e(B["ort"])}'
    t = (t.replace("{{BAR}}", bar).replace("{{ADDRESS}}", addr).replace("{{HOURS}}", hours_rows())
         .replace("{{HOURS_NOTE}}", e(H.get("hinweis", ""))).replace("{{TEL}}", TEL)
         .replace("{{TEL_TXT}}", e(B["telefon"])).replace("{{MAPS}}", e(MAPS))
         .replace("{{EYEBROW}}", e(f'{B["strasse"]} · {B["ort"]}'))
         .replace("{{SOCIAL}}", social()))
    t += f'<script id="hours-data" type="application/json">{hours_js()}</script>' + schema()
    return (head("Ponte Vecchio Regensburg | Bar, Café & Pizzeria",
                 "Pizza, Pasta, Kaffee und Drinks im Ponte Vecchio in Regensburg. Speisekarte, Öffnungszeiten, Adresse und telefonische Reservierung auf einen Blick.", "/")
            + header() + t + footer())


def price_html(p):
    return "<br>".join(e(x) for x in p.split(" · "))


def page_menu():
    nav, cats = [], []
    for k in M["kategorien"]:
        sid = "m-" + slug(k["titel"])
        nav.append(f'<a href="#{sid}">{e(k["titel"])}</a>')
        lis = []
        for g in k.get("gerichte", []):
            d = f'<p class="dish-d">{e(g["beschreibung"])}</p>' if g.get("beschreibung") else ""
            lis.append(f'<li class="dish"><div class="dish-h"><h3>{e(g["name"])}</h3><span class="lead" aria-hidden="true"></span>'
                       f'<span class="price">{price_html(g.get("preis", ""))}</span></div>{d}</li>')
        note = f'<p class="cat-note">{e(k["hinweis"])}</p>' if k.get("hinweis") else ""
        extra = ""
        if k.get("extras"):
            rows = "".join(f'<li><span class="price">je {e(x["preis"])}</span><span>{e(x["zutaten"])}</span></li>' for x in k["extras"])
            extra = f'<div class="extras"><h3>Extrazutaten</h3><ul>{rows}</ul></div>'
        cats.append(f'<section class="cat" id="{sid}" aria-labelledby="h-{sid}"><h2 id="h-{sid}">{e(k["titel"])}</h2>{note}'
                    f'<ul class="dishes">{"".join(lis)}</ul>{extra}</section>')
    foot = "".join(f"<p>{e(x.strip())}</p>" for x in re.split(r"(?<=\.)\s+", M.get("fusszeile", "")) if x.strip())
    body = f"""<div class="wrap menu-hero">
    <p class="eyebrow">Ponte Vecchio · {e(B['ort'])}</p>
    <h1 style="margin-top:.8rem">Speisekarte</h1>
    <p class="lede" style="margin-top:1rem">Alle Speisen vor Ort oder zum Mitnehmen. Reservierung unter <span style="white-space:nowrap">{e(B['telefon'])}</span>.</p>
  </div>
  <div class="wrap menu-strip">
    <div class="photo"><img src="/img/pizza-bresaola.jpg" alt="Pizza Rucola &amp; Bresaola auf kariertem Tischtuch" loading="lazy" decoding="async"></div>
    <div class="photo"><img src="/img/pasta-carbonara.jpg" alt="Penne Carbonara mit Speck und Parmesan" loading="lazy" decoding="async"></div>
    <div class="photo"><img src="/img/antipasti-platte.jpg" alt="Antipasti-Platte mit Bresaola, Schinken, Feigen und Rucola" loading="lazy" decoding="async"></div>
  </div>
  <nav class="menu-nav" aria-label="Kategorien der Speisekarte"><div class="wrap">{''.join(nav)}</div></nav>
  <div class="wrap menu-body">{''.join(cats)}</div>
  <div class="wrap menu-foot">{foot}</div>
"""
    return (head("Speisekarte | Ponte Vecchio Regensburg",
                 "Speisekarte des Ponte Vecchio in Regensburg: Pizza, Pasta, Vorspeisen, Salate, Desserts, Kaffee und Drinks mit Preisen.", "/speisekarte/")
            + header("menu") + body + footer())


def md(text):
    out = []
    for block in re.split(r"\n\s*\n", text.strip()):
        if block.startswith("## "):
            out.append(f"<h2>{e(block[3:].strip())}</h2>")
        else:
            out.append(f"<p>{e(block.strip())}</p>")
    return "".join(out)


def page_legal(kind):
    title = "Impressum" if kind == "impressum" else "Datenschutzerklärung"
    done = R.get(kind + "_fertig")
    todo = "" if done else ('<div class="todo"><b>Noch in Arbeit:</b> Diese Angaben werden vor der Veröffentlichung '
                            'mit den echten Daten des Inhabers ergänzt.</div>')
    body = f'<div class="wrap legal"><h1>{title}</h1>{todo}<div class="legal-body">{md(R.get(kind, ""))}</div></div>'
    return head(f"{title} | Ponte Vecchio Regensburg", f"{title} der Ponte Vecchio Bar & Pizzeria, Regensburg.", f"/{kind}/") \
        + header() + body + footer()


# ---------- Schriften (werden beim Build lokal gespeichert, kein Google-Abruf durch Besucher) ----------
FONTS = {
    "cormorant-500.woff2": "cormorant-garamond@latest/latin-500-normal.woff2",
    "cormorant-600.woff2": "cormorant-garamond@latest/latin-600-normal.woff2",
    "cormorant-500-italic.woff2": "cormorant-garamond@latest/latin-500-italic.woff2",
    "dmsans-400.woff2": "dm-sans@latest/latin-400-normal.woff2",
    "dmsans-500.woff2": "dm-sans@latest/latin-500-normal.woff2",
    "dmsans-600.woff2": "dm-sans@latest/latin-600-normal.woff2",
}


def fonts():
    dst = os.path.join(DIST, "fonts")
    os.makedirs(dst, exist_ok=True)
    for name, src in FONTS.items():
        local = os.path.join(ROOT, "static", "fonts", name)
        target = os.path.join(dst, name)
        if os.path.exists(local):
            shutil.copy(local, target)
            continue
        try:
            urllib.request.urlretrieve("https://cdn.jsdelivr.net/fontsource/fonts/" + src, target)
        except Exception as ex:  # Seite funktioniert trotzdem, mit Ersatzschrift
            print("Hinweis: Schrift nicht geladen:", name, ex)


def write(path, content):
    full = os.path.join(DIST, path.strip("/"), "index.html") if path != "/" else os.path.join(DIST, "index.html")
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)


def main():
    if os.path.exists(DIST):
        shutil.rmtree(DIST)
    os.makedirs(os.path.join(DIST, "img"), exist_ok=True)
    os.makedirs(os.path.join(DIST, "admin"), exist_ok=True)
    if os.path.isdir(os.path.join(ROOT, "static")):
        shutil.copytree(os.path.join(ROOT, "static"), DIST, ignore=shutil.ignore_patterns("fonts"), dirs_exist_ok=True)
    if os.path.isdir(os.path.join(ROOT, "admin")):
        shutil.copytree(os.path.join(ROOT, "admin"), os.path.join(DIST, "admin"), dirs_exist_ok=True)
    # Dateien, die lose in der Hauptebene liegen
    for f in os.listdir(ROOT):
        src = os.path.join(ROOT, f)
        if not os.path.isfile(src):
            continue
        low = f.lower()
        if low.endswith((".jpg", ".jpeg", ".png", ".webp", ".gif")):
            shutil.copy(src, os.path.join(DIST, "img", f))
        elif f in ("style.css", "main.js", "favicon.svg"):
            shutil.copy(src, os.path.join(DIST, f))
        elif f in ("index.html", "config.yml"):
            shutil.copy(src, os.path.join(DIST, "admin", f))
    fonts()
    write("/", page_home())
    write("/speisekarte/", page_menu())
    write("/impressum/", page_legal("impressum"))
    write("/datenschutz/", page_legal("datenschutz"))
    with open(os.path.join(DIST, "robots.txt"), "w") as f:
        f.write("User-agent: *\nDisallow: /admin/\n" + (f"Sitemap: {DOMAIN}/sitemap.xml\n" if INDEX else "Disallow: /\n"))
    urls = "".join(f"<url><loc>{e(DOMAIN)}{p}</loc></url>" for p in ["/", "/speisekarte/", "/impressum/", "/datenschutz/"])
    with open(os.path.join(DIST, "sitemap.xml"), "w") as f:
        f.write(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>')
    print("Fertig: dist/")


if __name__ == "__main__":
    main()
