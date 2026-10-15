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
O = load("bestellung.json")
RV = load("bewertungen.json")
AL = load("allergene.json")
AL_PATH = "/allergene-und-zusatzstoffe/"

DOMAIN = B.get("domain", "").rstrip("/")
INDEX = bool(B.get("suchmaschinen_freigeben"))
TEL = "+" + re.sub(r"\D", "", B["telefon"])
ADDR_Q = f'{B["name"]}, {B["strasse"]}, {B["plz"]} {B["ort"]}'
MAPS = "https://www.google.com/maps/search/?api=1&query=" + urllib.parse.quote_plus(ADDR_Q)
# Meta Pixel: nur Ziffern erlaubt. Leer = kein Pixel und kein Cookie-Banner.
PIXEL = re.sub(r"\D", "", str(B.get("meta_pixel_id", "")))


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
      <a class="nl" href="/bestellen/"{cur('order')}>Abholung bestellen</a>
      <a class="btn btn-gold" href="/reservieren/"{cur('reserve')}>Reservieren</a>
    </nav>
  </div>
</header>
<main id="main">
"""


IG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r="1" fill="currentColor" stroke="none"/></svg>'
FB = '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M14 8h3V4h-3c-2.8 0-4.5 1.8-4.5 4.6V11H7v4h2.5v6h4v-6h3l.5-4h-3.5V8.8c0-.5.3-.8.5-.8z"/></svg>'


def social():
    """Nur einfache Links: keine Einbettung, keine Cookies."""
    out = []
    if B.get("instagram", "").strip():
        out.append(f'<a class="soc" href="{e(B["instagram"].strip())}" target="_blank" rel="noopener" aria-label="Ponte Vecchio auf Instagram">{IG}<span>Instagram</span></a>')
    if B.get("facebook", "").strip():
        out.append(f'<a class="soc" href="{e(B["facebook"].strip())}" target="_blank" rel="noopener" aria-label="Ponte Vecchio auf Facebook">{FB}<span>Facebook</span></a>')
    return f'<div class="socials">{"".join(out)}</div>' if out else ""


def consent():
    """Cookie-Banner für den Meta Pixel. Der Pixel lädt erst nach Klick auf „Akzeptieren“."""
    if not PIXEL:
        return ""
    cfg = json.dumps({"pixel": PIXEL})
    return f"""<div class="cc" id="cc" role="dialog" aria-modal="false" aria-labelledby="cc-t" hidden>
  <div class="cc-box">
    <p class="cc-t" id="cc-t">Cookies &amp; Werbung</p>
    <p class="cc-x">Mit Ihrer Zustimmung nutzen wir den Meta Pixel (Facebook/Instagram), um zu messen, wie gut unsere Werbung wirkt, und um Ihnen passende Anzeigen zu zeigen. Dabei werden Daten an Meta übermittelt, auch in die USA. Ohne Zustimmung funktioniert die Website genauso. Sie können Ihre Wahl jederzeit unten auf der Seite unter „Cookie-Einstellungen“ ändern. Mehr in der <a href="/datenschutz/">Datenschutzerklärung</a>.</p>
    <div class="cc-b">
      <button type="button" class="btn btn-ghost" data-cc="no">Ablehnen</button>
      <button type="button" class="btn btn-ghost" data-cc="yes">Akzeptieren</button>
    </div>
  </div>
</div>
<script id="consent-cfg" type="application/json">{cfg}</script>
"""


def footer(mbar=True):
    cc_link = '<li><button type="button" class="linkbtn" data-cc="open">Cookie-Einstellungen</button></li>' if PIXEL else ""
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
      <ul><li><a href="/">Startseite</a></li><li><a href="/speisekarte/">Speisekarte</a></li><li><a href="/bestellen/">Abholung bestellen</a></li><li><a href="/reservieren/">Tisch reservieren</a></li><li><a href="/#zeiten">Öffnungszeiten</a></li><li><a href="/#kontakt">Kontakt</a></li></ul>
    </div>
    <div>
      <h3>Rechtliches</h3>
      <ul><li><a href="/impressum/">Impressum</a></li><li><a href="/datenschutz/">Datenschutz</a></li><li><a href="{AL_PATH}">Allergene &amp; Zusatzstoffe</a></li>{cc_link}</ul>
    </div>
    <p class="copy">© {date.today().year} {e(B['name'])}</p>
  </div>
</footer>
{MBAR if mbar else ""}
{consent()}<script src="/main.js" defer></script>
</body>
</html>
"""


MBAR = f"""<nav class="mbar" aria-label="Schnellaktionen">
  <a href="/speisekarte/"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M5 4h11a3 3 0 0 1 3 3v13H8a3 3 0 0 1-3-3z"/><path d="M9 9h6M9 13h6"/></svg>Speisekarte</a>
  <a href="tel:{TEL}"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2"/></svg>Anrufen</a>
  <a href="{e(MAPS)}" target="_blank" rel="noopener"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M12 21s-7-6.2-7-11.5A7 7 0 0 1 19 9.5C19 14.8 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/></svg>Route</a>
</nav>"""


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


# ---------- Bewertungen (Auswahl echter Google-Bewertungen + Bewerten-Button) ----------
GOOGLE_G = '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="#4285F4" d="M22.6 12.2c0-.8-.1-1.5-.2-2.2H12v4.2h6a5.1 5.1 0 0 1-2.2 3.4v2.8h3.6c2.1-1.9 3.2-4.8 3.2-8.2z"/><path fill="#34A853" d="M12 23c3 0 5.5-1 7.4-2.7l-3.6-2.8c-1 .7-2.3 1.1-3.8 1.1-2.9 0-5.4-2-6.3-4.6H2v2.9A11 11 0 0 0 12 23z"/><path fill="#FBBC05" d="M5.7 14a6.6 6.6 0 0 1 0-4.2V7H2a11 11 0 0 0 0 9.9z"/><path fill="#EA4335" d="M12 5.4c1.6 0 3.1.6 4.2 1.7l3.2-3.2A11 11 0 0 0 2 7l3.7 2.9C6.6 7.3 9.1 5.4 12 5.4z"/></svg>'


def review_links():
    pid = RV.get("google_place_id", "").strip()
    direct = RV.get("google_bewerten_link", "").strip()
    write = direct or (f"https://search.google.com/local/writereview?placeid={urllib.parse.quote(pid)}" if pid else MAPS)
    show = RV.get("google_link", "").strip() or (f"https://search.google.com/local/reviews?placeid={urllib.parse.quote(pid)}" if pid else MAPS)
    return write, show


def stars(n):
    n = max(0, min(5, int(n or 0)))
    return f'<span class="rv-stars" role="img" aria-label="{n} von 5 Sternen">{"★" * n}<span class="rv-off">{"★" * (5 - n)}</span></span>'


def reviews_section():
    if not RV.get("anzeigen"):
        return ""
    write, show = review_links()
    cards = []
    for r in RV.get("bewertungen", [])[:6]:
        img = (f'<div class="photo rv-photo"><img src="{e(r["bild"])}" alt="{e(r.get("bild_alt", ""))}" loading="lazy" decoding="async"></div>'
               if r.get("bild", "").strip() else "")
        tag = '<span class="rv-demo">Beispiel</span>' if r.get("beispiel") else ""
        cards.append(f'<li class="rv-card">{img}<div class="rv-body"><div class="rv-top">{stars(r.get("sterne", 5))}{tag}</div>'
                     f'<p class="rv-text">{e(r.get("text", ""))}</p>'
                     f'<p class="rv-by"><b>{e(r.get("name", ""))}</b><span>{e(r.get("datum", ""))} · Google</span></p></div></li>')
    avg = RV.get("durchschnitt", "").strip()
    cnt = RV.get("anzahl", "").strip()
    avg_ok = bool(re.match(r"^[0-5]([.,][0-9])?$", avg))
    avg_stars = stars(round(float(avg.replace(",", ".")))) if avg_ok else ""
    cnt_txt = e(cnt) + " Bewertungen " if cnt else ""
    score = f'<p class="rv-score"><b>{e(avg)}</b>{avg_stars}<span>{cnt_txt}auf Google</span></p>' if avg else ""
    return f"""
  <section class="sec" id="bewertungen" aria-labelledby="rv-h">
    <div class="wrap">
      <div class="rv-head">
        <div class="sec-head" style="margin:0">
          <p class="eyebrow">Bewertungen</p>
          <h2 id="rv-h">{e(RV.get("ueberschrift", "Was unsere Gäste sagen"))}</h2>
          {score}
        </div>
        <div class="cta-row">
          <a class="btn btn-gold" href="{e(write)}" target="_blank" rel="noopener">{GOOGLE_G}Auf Google bewerten</a>
          <a class="btn btn-ghost" href="{e(show)}" target="_blank" rel="noopener">Alle Bewertungen</a>
        </div>
      </div>
      <ul class="rv-list rv-n{len(cards)}">{"".join(cards)}</ul>
      <p class="rv-note">Ausgewählte Bewertungen von Gästen auf Google. Alle Bewertungen finden Sie auf unserem Google-Profil.</p>
    </div>
  </section>
"""


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
         .replace("{{SOCIAL}}", social()).replace("{{REVIEWS}}", reviews_section()))
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
    foot += f'<p><a class="al-link" href="{AL_PATH}">Allergene &amp; Zusatzstoffe ansehen <span aria-hidden="true">→</span></a></p>'
    body = f"""<div class="wrap menu-hero">
    <p class="eyebrow">Ponte Vecchio · {e(B['ort'])}</p>
    <h1 style="margin-top:.8rem">Speisekarte</h1>
    <p class="lede" style="margin-top:1rem">Alle Speisen vor Ort oder zum Mitnehmen.</p>
    <div class="cta-row" style="margin-top:1.4rem"><a class="btn btn-gold" href="/bestellen/">Abholung bestellen</a><a class="btn btn-ghost" href="/reservieren/">Tisch reservieren</a></div>
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


def page_allergene():
    legend = []
    for a in AL.get("allergene", []):
        sub = f'<span class="al-sub">{e(a["unterteilung"])}</span>' if a.get("unterteilung", "").strip() else ""
        legend.append(f'<li><span class="al-code">{e(a["code"])}</span><span><span class="al-name">{e(a["name"])}</span>{sub}</span></li>')
    cats = []
    for k in AL.get("kategorien", []):
        sid = "a-" + slug(k["titel"])
        note = f'<p class="cat-note">{e(k["hinweis"])}</p>' if k.get("hinweis", "").strip() else ""
        lis = "".join(f'<li class="dish"><div class="dish-h"><h3>{e(g["name"])}</h3><span class="lead" aria-hidden="true"></span>'
                      f'<span class="price">{e(g.get("kennzeichnung", ""))}</span></div></li>' for g in k.get("gerichte", []))
        cats.append(f'<section class="cat" id="{sid}" aria-labelledby="h-{sid}"><h2 id="h-{sid}">{e(k["titel"])}</h2>{note}'
                    f'<ul class="dishes">{lis}</ul></section>')
    fn = f'<p>{e(AL["fussnote"])}</p>' if AL.get("fussnote", "").strip() else ""
    ask = AL.get("schlusshinweis", "").strip()
    ask = f'<div class="al-ask"><p class="al-ask-t">{e(ask)}</p></div>' if ask else ""
    body = f"""<div class="wrap menu-hero">
    <p class="eyebrow">Ponte Vecchio · {e(B['ort'])}</p>
    <h1 style="margin-top:.8rem">Allergene und Zusatzstoffe</h1>
    <p class="lede" style="margin-top:1rem">{e(AL.get('einleitung', ''))}</p>
  </div>
  <div class="wrap">
    <section class="al-legend" aria-labelledby="h-allergene"><h2 id="h-allergene">Allergene</h2><ul>{''.join(legend)}</ul></section>
  </div>
  <div class="wrap menu-body">{''.join(cats)}</div>
  <div class="wrap menu-foot">{fn}{ask}<p><a class="al-link" href="/speisekarte/">Zur Speisekarte <span aria-hidden="true">→</span></a></p></div>
"""
    return (head("Allergene und Zusatzstoffe | Ponte Vecchio Regensburg",
                 "Allergene und Zusatzstoffe der Speisen im Ponte Vecchio in Regensburg: Vorspeisen, Pasta, Pizza, Hauptspeisen und Desserts.", AL_PATH)
            + header() + body + footer())


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


# ---------- Bestellen & Reservieren (per WhatsApp) ----------
def euro(t):
    """'12,00 €' -> 12.0; mehrere Preise oder kein Preis -> None"""
    m = re.findall(r"(\d+)(?:,(\d{1,2}))?\s*€", t or "")
    if len(m) != 1:
        return None
    return int(m[0][0]) + int((m[0][1] or "0").ljust(2, "0")) / 100


def parts(t):
    return [x.strip() for x in re.split(r",\s*|\s+oder\s+|\s+&\s+", t or "") if x.strip()]


def order_data():
    skip_cat = set(O.get("kategorien_ausblenden", []))
    skip = set(O.get("nicht_bestellbar", []))
    hot = {"label": "Schärfe", "type": "many", "hint": "optional, kostenlos", "plain": True,
           "choices": [{"n": "Scharf (Chiliöl)"}]}
    parm = {"label": "Parmesan", "type": "one",
            "choices": [{"n": "Ohne Parmesan"}, {"n": "Mit Parmesan"},
                        {"n": "Extra Parmesan", "p": euro(O.get("parmesan_extra_preis", "")) or 2.0}]}
    menu = []
    for k in M["kategorien"]:
        if k["titel"] in skip_cat:
            continue
        is_pizza = k["titel"] == O.get("pizza_kategorie")
        is_pasta = k["titel"] == O.get("pasta_kategorie")
        extras = None
        if is_pizza and k.get("extras"):
            ch = [{"n": z, "p": euro(x["preis"])} for x in k["extras"] for z in parts(x["zutaten"])]
            extras = {"label": "Extrazutaten", "type": "many", "hint": "optional, mehrere möglich", "choices": ch}
        noodles = None
        mm = re.search(r"\bmit\s+(.+)$", k.get("hinweis", "")) if is_pasta else None
        if mm:
            noodles = {"label": "Nudelsorte", "type": "one", "choices": [{"n": x} for x in parts(mm.group(1))]}
        items = []
        for g in k.get("gerichte", []):
            name, desc = g["name"].strip(), (g.get("beschreibung") or "").strip()
            if name in skip or f"{name} {desc}".strip() in skip:
                continue
            p = euro(g.get("preis", ""))
            if p is None:
                print("Hinweis: nicht online bestellbar (Preis unklar):", name)
                continue
            it = {"n": name, "d": desc, "p": p, "groups": []}
            if is_pizza:
                it["prefix"] = "Pizza"
                it["groups"] = ([extras] if extras else []) + [hot]
            elif is_pasta:
                if noodles and name not in O.get("pasta_ohne_nudelwahl", []):
                    it["prefix"] = "Pasta"
                    it["groups"].append(noodles)
                it["groups"] += [parm, hot]
            elif ", " in name:  # mehrere Sorten in einer Zeile, z. B. Softdrinks
                it["groups"].append({"label": "Sorte", "type": "one", "choices": [{"n": x} for x in name.split(", ")]})
                it["useChoice"], it["size"] = True, desc
            else:
                m2 = re.match(r".*\bmit\s+(.+?)\s+oder\s+(.+)$", desc)  # z. B. „mit Pommes oder Kartoffelpüree“
                if m2:
                    it["groups"].append({"label": "Beilage", "type": "one", "choices": [{"n": m2.group(1)}, {"n": m2.group(2)}]})
            items.append(it)
        for a in O.get("zusaetzlich", []):
            if a.get("kategorie") == k["titel"] and euro(a.get("preis")) is not None:
                it = {"n": a["name"], "d": a.get("beschreibung", ""), "p": euro(a["preis"]), "groups": []}
                if a.get("auswahl"):
                    it["groups"].append({"label": "Sorte", "type": "one", "choices": [{"n": x} for x in parts(a["auswahl"])]})
                    it["useChoice"] = True
                    it["size"] = a.get("groesse") or a.get("beschreibung", "").split("·")[-1].strip()
                items.append(it)
        if items:
            menu.append({"id": slug(k["titel"]), "name": k["titel"], "note": k.get("hinweis", ""), "items": items,
                         "extras": k.get("extras") if is_pizza else None})
    wa = re.sub(r"\D", "", O.get("whatsapp") or B["telefon"])
    settings = {"wa": wa, "waText": O.get("whatsapp") or B["telefon"],
                "lead": int(O.get("vorlauf_minuten", 30)), "last": int(O.get("letzte_zeit_minuten_vor_schluss", 30)),
                "step": int(O.get("takt_minuten", 15)), "resDays": int(O.get("reservierung_tage_im_voraus", 14)),
                "maxP": int(O.get("max_personen", 8)),
                "hours": [[[mins(x["von"]), mins(x["bis"])] for x in (d.get("zeiten") or [])] for d in H["tage"]],
                "days": [d["tag"] for d in H["tage"]]}
    js = json.dumps({"menu": menu, "settings": settings}, ensure_ascii=False).replace("</", "<\\/")
    return f'<script id="order-data" type="application/json">{js}</script>'


WAIT_NOTE = (f'Nach dem Absenden bitte auf unsere Antwort im Chat warten. Falls innerhalb von 5 Minuten keine Antwort kommt, '
             f'bitte anrufen: <span style="white-space:nowrap">{e(O.get("whatsapp") or B["telefon"])}</span>.')
PAY_NOTE = '<p class="o-pay"><b>Bezahlung vor Ort</b> · bar oder mit Karte: EC-Karte, Visa, Mastercard, American Express und weitere</p>'


def page_order():
    body = f"""<div class="wrap o-hero">
    <p class="eyebrow">Online bestellen · {e(B['strasse'])}</p>
    <h1 id="o-title">Abholung bestellen</h1>
    <p class="lede" id="o-lead">Gerichte mit + auswählen, unten auf den Warenkorb tippen, Abholzeit wählen und per WhatsApp abschicken. Wir bestätigen Ihre Bestellung im Chat.</p>
    <div class="o-table" id="o-table" hidden><p id="o-table-txt"></p><a class="o-link" href="/reservieren/">Ändern</a></div>
    {PAY_NOTE}
  </div>
  <nav class="menu-nav" aria-label="Kategorien"><div class="wrap" id="o-chips"></div></nav>
  <div class="wrap menu-body" id="o-menu"></div>
  <div class="wrap menu-foot"><p>{WAIT_NOTE}</p><p>Alle Preise in Euro inkl. MwSt.</p><p><a class="al-link" href="{AL_PATH}">Allergene &amp; Zusatzstoffe ansehen <span aria-hidden="true">→</span></a></p></div>
  <div class="o-bar"><div class="wrap"><button type="button" class="o-barbtn o-empty" id="o-open"><span><span class="o-cnt" id="o-cnt">0</span><span id="o-barlbl">Noch nichts ausgewählt</span></span><span id="o-sum">0,00 €</span></button></div></div>
  <div class="o-scrim" id="o-opt" hidden><div class="o-sheet" role="dialog" aria-modal="true" aria-labelledby="o-opt-t" id="o-optbox"></div></div>
  <div class="o-scrim" id="o-cart" hidden><div class="o-sheet" role="dialog" aria-modal="true" aria-labelledby="o-cart-t" id="o-cartbox"></div></div>
  {order_data()}<script src="/bestellen.js" defer></script>
"""
    return (head("Abholung bestellen | Ponte Vecchio Regensburg",
                 "Pizza, Pasta und mehr im Ponte Vecchio Regensburg online auswählen und per WhatsApp zur Abholung bestellen.", "/bestellen/")
            .replace("<body>", '<body data-page="bestellen">') + header("order") + body + footer(mbar=False))


def page_reserve():
    body = f"""<div class="wrap o-hero o-narrow">
    <p class="eyebrow">Tisch reservieren · {e(B['strasse'])}</p>
    <h1>Tisch reservieren</h1>
    <p class="lede">Tag, Uhrzeit und Personenzahl wählen und per WhatsApp senden. Auf Wunsch bestellen Sie Ihr Essen gleich mit vor. Wir bestätigen Ihre Reservierung im Chat.</p>
  </div>
  <div class="wrap o-narrow o-form">
    <section class="o-sec"><h2>Tag</h2><div class="o-days" id="r-days"></div></section>
    <section class="o-sec"><h2>Uhrzeit</h2><div id="r-times"></div></section>
    <section class="o-sec"><h2>Personen</h2><div class="o-opts" id="r-persons"></div>
      <p class="o-sub">Kinderstuhl</p><div class="o-opts" id="r-kids"></div></section>
    <section class="o-sec"><h2>Ihre Angaben</h2>
      <div class="o-fld"><label for="r-name">Name</label><input id="r-name" autocomplete="name" placeholder="z. B. Maria Huber"></div>
      <div class="o-fld"><label for="r-note">Anmerkung (optional)</label><textarea id="r-note" placeholder="z. B. Geburtstag, Terrasse gewünscht"></textarea></div>
    </section>
    <section class="o-sec"><h2>Essen vorbestellen?</h2>
      <p class="o-muted o-small">Wenn Sie möchten, wählen Sie Ihr Essen schon jetzt aus. Wir bereiten es zu Ihrer Ankunft vor.</p>
      <div class="o-opts" id="r-food"></div></section>
    <div class="o-res-sum"><h3>Ihre Reservierung</h3><p id="r-sum"></p></div>
    <p class="o-err" id="r-err" hidden></p>
    <a class="o-wa o-send" id="r-send" href="#" target="_blank" rel="noopener">Per WhatsApp reservieren</a>
    <div id="r-hint"><p class="o-hint">WhatsApp öffnet sich mit Ihrer fertigen Anfrage an {e(O.get("whatsapp") or B["telefon"])}. Sie müssen nur noch auf Senden tippen.</p></div>
    <p class="o-hint">{WAIT_NOTE}</p>
    <p class="o-hint">Die Reservierung gilt erst nach unserer Bestätigung. Gruppen ab {int(O.get("max_personen", 8)) + 1} Personen bitte telefonisch anfragen: <a href="tel:{TEL}">{e(B['telefon'])}</a>.</p>
  </div>
  {order_data()}<script src="/bestellen.js" defer></script>
"""
    return (head("Tisch reservieren | Ponte Vecchio Regensburg",
                 "Tisch im Ponte Vecchio Regensburg online auswählen und per WhatsApp reservieren, auf Wunsch mit vorbestelltem Essen.", "/reservieren/")
            .replace("<body>", '<body data-page="reservieren">') + header("reserve") + body + footer(mbar=False))


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
        elif f in ("style.css", "main.js", "bestellen.js", "favicon.svg"):
            shutil.copy(src, os.path.join(DIST, f))
        elif f in ("index.html", "config.yml"):
            shutil.copy(src, os.path.join(DIST, "admin", f))
    fonts()
    write("/", page_home())
    write("/speisekarte/", page_menu())
    write("/bestellen/", page_order())
    write("/reservieren/", page_reserve())
    write("/impressum/", page_legal("impressum"))
    write("/datenschutz/", page_legal("datenschutz"))
    write(AL_PATH, page_allergene())
    with open(os.path.join(DIST, "robots.txt"), "w") as f:
        f.write("User-agent: *\nDisallow: /admin/\n" + (f"Sitemap: {DOMAIN}/sitemap.xml\n" if INDEX else "Disallow: /\n"))
    urls = "".join(f"<url><loc>{e(DOMAIN)}{p}</loc></url>" for p in ["/", "/speisekarte/", "/bestellen/", "/reservieren/", AL_PATH, "/impressum/", "/datenschutz/"])
    with open(os.path.join(DIST, "sitemap.xml"), "w") as f:
        f.write(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>')
    print("Fertig: dist/")


if __name__ == "__main__":
    main()
