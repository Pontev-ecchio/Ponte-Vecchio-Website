
# Ponte Vecchio Website – Einrichtung & Bedienung

**Grundregel:** Alle Konten (GitHub, Netlify, Domain) laufen auf den **Inhaber** und seine E-Mail-Adresse.
Anton (Designer) bekommt nur einen **Mitarbeiter-Zugang**. Er kann Inhalte und Design bearbeiten, aber nichts löschen, was dem Inhaber gehört, und der Inhaber kann ihm den Zugang jederzeit wieder entziehen.

| | Inhaber | Anton |
|---|---|---|
| Eigentümer von Domain, Hosting, Code | ✔ | – |
| Admin-Bereich `/admin` (Speisekarte, Zeiten, Kontakt …) | ✔ | ✔ |
| Mitarbeiter hinzufügen oder entfernen | ✔ | – |
| Rechnungen / Zahlungsdaten | ✔ | – |

Kosten: GitHub und Netlify sind im Grundtarif kostenlos. Nur die Domain kostet etwas (meist ca. 10–20 € pro Jahr).

---

## Vorbereitung (bevor ihr euch trefft)

**Anton:**
- Eigenes GitHub-Konto anlegen (github.com, kostenlos), falls noch nicht vorhanden. Den Benutzernamen notieren.
- Die Datei `ponte-vecchio-website.zip` auf einen USB-Stick oder in die Cloud legen, damit ihr sie am Laptop des Inhabers habt.

**Inhaber:**
- Laptop mit Chrome oder Edge, geladen
- E-Mail-Adresse fürs Geschäft, mit Zugriff aufs Postfach (für Bestätigungsmails)
- Handy (für die Zwei-Faktor-Anmeldung)
- Zahlungsmittel für die Domain (Karte oder PayPal)
- Wunsch-Domain überlegen, z. B. `ponte-vecchio-regensburg.de`
- Daten fürs Impressum: vollständiger Vor- und Nachname (bzw. Firma mit Rechtsform), Anschrift, Telefon, E-Mail. USt-ID und Handelsregister **nur, falls vorhanden**. Die Steuernummer kommt nicht ins Impressum.

**Dateien auf den Laptop des Inhabers bringen** (vom MacBook aus, eine Möglichkeit reicht):
- **Per E-Mail (empfohlen):** Die ZIP-Datei (ca. 5 MB) an die Geschäfts-E-Mail des Inhabers schicken und am Laptop herunterladen. So testet ihr gleich, dass die E-Mail funktioniert.
- **USB-Stick:** Ein Stick im Format „ExFAT“ funktioniert mit Mac und Windows.
- AirDrop geht nur zwischen Apple-Geräten.

**Vor dem Hochladen:** Die ZIP-Datei am Laptop entpacken (Rechtsklick → „Alle extrahieren“). Hochgeladen wird der **Inhalt** des entpackten Ordners, nicht die ZIP-Datei selbst.

---

## Teil A – Einmalige Einrichtung (Inhaber und Anton zusammen am Laptop des Inhabers, ca. 45 Min.)

### 1. GitHub-Konto für den Inhaber
1. Auf **github.com** mit der geschäftlichen E-Mail des Inhabers registrieren.
2. Zwei-Faktor-Anmeldung einschalten (Settings → Password and authentication).

### 2. Projekt anlegen
1. Oben rechts **+ → New repository**.
2. Name: `ponte-vecchio-website`, Sichtbarkeit: **Private**, dann **Create repository**.
3. **Settings → Collaborators → Add people** und Antons GitHub-Namen einladen. Anton bestätigt die Einladung per E-Mail.
4. Anton lädt den Inhalt dieses Ordners hoch (**Add file → Upload files**, alle Dateien und Ordner hineinziehen, dann **Commit changes**).

### 3. Netlify (Hosting) für den Inhaber
1. Auf **netlify.com** auf **Sign up** und dann **mit GitHub anmelden** klicken (mit dem Konto des Inhabers).
2. **Add new project → Import an existing project → GitHub** und das Projekt `ponte-vecchio-website` auswählen.
3. Die Einstellungen werden automatisch aus `netlify.toml` gelesen. Einfach auf **Deploy** klicken.
4. Nach 1–2 Minuten ist die Seite unter einer Adresse wie `irgendwas.netlify.app` erreichbar. Diese Adresse notieren.

### 4. Login für den Admin-Bereich freischalten
1. Bei GitHub (Konto des Inhabers): **Settings → Developer settings → OAuth Apps → New OAuth App**
   - Application name: `Ponte Vecchio Admin`
   - Homepage URL: die Netlify-Adresse aus Schritt 3
   - Authorization callback URL: `https://api.netlify.com/auth/done`
   - **Register application**, dann **Generate a new client secret**. Client ID und Secret kopieren.
2. Bei Netlify: im Projekt **Project configuration → Security → OAuth** → unter *Authentication Providers* **Install Provider** → **GitHub**. Client ID und Secret einfügen, speichern.
3. In der Datei `admin/config.yml` die Zeile `repo:` anpassen, z. B. `repo: inhabername/ponte-vecchio-website`. Das geht direkt auf GitHub über das Stift-Symbol.

### 5. Testen
`https://<netlify-adresse>/admin` öffnen und auf **Mit GitHub anmelden** klicken. Beide, Inhaber und Anton, sollten sich einloggen können.

### 6. Eigene Domain (auf den Namen des Inhabers)
1. Domain kaufen, z. B. `ponte-vecchio-regensburg.de`. Das geht direkt bei Netlify (**Domain management → Add a domain**) oder bei einem Anbieter wie IONOS oder Strato. Wichtig: **Inhaber als Domaininhaber** eintragen.
2. In Netlify unter **Domain management** die Domain verbinden. HTTPS wird automatisch eingerichtet.
3. Im Admin-Bereich unter **Kontakt & Grunddaten → Domain** die echte Adresse eintragen und in `admin/config.yml` bei `site_url` und `display_url` ebenso.
4. In der GitHub-OAuth-App (Schritt 4) die Homepage URL auf die neue Domain ändern.

### 7. Instagram & Facebook verlinken
Im Admin-Bereich unter **Kontakt & Grunddaten** die beiden Profil-Links eintragen und auf **Veröffentlichen** klicken. Die Symbole erscheinen dann bei Kontakt und im Footer.
Das sind bewusst nur Links, keine eingebetteten Feeds. Deshalb setzt die Website weiterhin **keine Cookies** und braucht **kein Cookie-Banner**.
In beiden Profilen in der Beschreibung bzw. im Info-Bereich die Website und das Impressum verlinken (`https://<domain>/impressum/`). Geschäftliche Profile brauchen in Deutschland ein Impressum.

### 8. Google-Unternehmensprofil (Google Maps)
1. Mit dem **Google-Konto des Inhabers** auf **business.google.com** gehen. Falls es noch kein Konto gibt, eines mit der Geschäfts-E-Mail anlegen.
2. Prüfen, ob „Ponte Vecchio Bar & Pizzeria“ in der Straubinger Str. 81 schon auf Google Maps existiert. Wenn ja, **„Inhaberschaft beanspruchen“** wählen. Wenn nein, ein neues Profil anlegen.
3. Kategorie: **Pizzeria**, dazu als weitere Kategorien z. B. **Bar** und **Café**.
4. Adresse, Telefon, Öffnungszeiten, Website-Adresse (sobald die Domain läuft) und Speisekarten-Link (`https://<domain>/speisekarte/`) eintragen.
5. **Bestätigen:** Google verlangt eine Verifizierung, oft per kurzem Video vom Lokal mit Schild, Eingang und Innenraum. Das kann einige Tage dauern.
6. Fotos hochladen. Die gleichen wie auf der Website eignen sich gut.
7. **Anton als Manager hinzufügen:** Profil → **Einstellungen → Personen und Zugriff → Hinzufügen** → Antons E-Mail → Rolle **Manager**. Der Inhaber bleibt **Hauptinhaber**.

Wichtig: Öffnungszeiten-Änderungen immer an **beiden** Stellen machen, auf der Website (Admin-Bereich) und im Google-Profil.

---

## Teil B – Bedienung im Alltag (für den Inhaber)

1. `https://www.<eure-domain>.de/admin` öffnen und **Mit GitHub anmelden**.
2. Links einen Bereich wählen:
   - **Öffnungszeiten:** Zeiten je Tag. Zeiten leer lassen bedeutet Ruhetag. Unter „Sonderhinweis“ erscheint ein Hinweis oben auf der Seite, z. B. „Betriebsurlaub vom 1.–14. August“.
   - **Speisekarte:** Gerichte ändern, hinzufügen (**Hinzufügen**), löschen (Papierkorb) oder per Ziehen umsortieren.
   - **Kontakt & Grunddaten:** Telefon, Adresse, Bar-Preise auf der Startseite.
   - **Impressum & Datenschutz.**
3. Oben auf **Veröffentlichen** klicken. Nach etwa 1–2 Minuten ist die Änderung online.

Die „Jetzt geöffnet / Gerade geschlossen“-Anzeige auf der Startseite rechnet automatisch mit den eingetragenen Zeiten.

Jede Änderung wird gespeichert. Falls etwas schiefgeht, kann Anton jede frühere Version wiederherstellen.

---

## Teil C – Vor dem offiziellen Start (Checkliste)

1. Impressum mit echten Daten ausfüllen (vollständiger Name bzw. Firma mit Rechtsform, Anschrift, Telefon, E-Mail; USt-ID und Handelsregister nur, falls vorhanden; empfohlen: zuständige Behörde der Gaststättenerlaubnis) und den Schalter **„Impressum ist vollständig“** einschalten.
2. Datenschutzerklärung für die tatsächlich genutzten Dienste erstellen (Hosting: Netlify; Schriften: lokal eingebunden, kein Google-Fonts-Abruf; Google-Maps-Link nur als Link; keine Analyse-Tools, solange keine eingebaut sind). Danach den Schalter **„… ist vollständig“** einschalten.
3. Domain eintragen (siehe A6).
4. **Kontakt & Grunddaten → „Bei Google sichtbar machen“** einschalten. Erst dann wird die Seite für Suchmaschinen freigegeben und die Sitemap aktiv.
5. Auf Handy und Laptop testen: Anrufen-Button, Route, Speisekarte, alle Menüpunkte.
6. Im **Google-Unternehmensprofil** die neue Website eintragen (Konto des Inhabers, Anton nur als Manager).
7. Google Ads erst danach auf die fertige Domain schicken.

---

## Technischer Aufbau (für Anton)

```
content/        Inhalte als JSON (werden im Admin-Bereich bearbeitet)
templates_home.html  Aufbau der Startseite
static/         style.css, main.js, favicon.svg, img/ (Fotos)
admin/          Admin-Bereich (Decap CMS, Login über GitHub)
build.py        erzeugt die fertige Website in dist/
netlify.toml    Build-Einstellungen für Netlify
```

- Lokal testen: `python3 build.py`, dann `dist/` mit einem beliebigen Webserver öffnen, z. B. `python3 -m http.server -d dist`.
- Schriften: Werden beim Build einmal von jsDelivr geladen und **lokal auf der eigenen Domain** ausgeliefert. Besucher verbinden sich also nicht mit Google. Alternativ die `.woff2`-Dateien in `static/fonts/` legen.
- Neue Fotos: über den Admin-Bereich hochladen landen sie in `static/img/`. Welche Fotos an welcher Stelle der Startseite stehen, legt `templates_home.html` fest.
