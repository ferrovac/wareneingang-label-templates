# Wareneingang – Etiketten-Vorlagen

Etiketten-Vorlagen für den Wareneingang der Ferrovac AG, gedruckt auf Brother-QL-Etikettendruckern
(Endlosband 62 mm und 38 mm). *Label templates for goods receipt, printed on Brother QL label
printers; SVG with Jinja placeholders.*

Jede Vorlage ist **eine SVG-Datei** mit Platzhaltern. Die Wareneingangs-App füllt die
Platzhalter mit den Daten der eingebuchten Position, zeigt eine Vorschau und druckt auf dem
gewählten Drucker. Angeboten werden nur Vorlagen, deren Rollenbreite zum Drucker passt: **es muss ein Drucker
mit dieser Rolle als aktiver Drucker ausgewählt sein** ("Auswählen" in der App – die Rolle
meldet der Drucker selbst). Eine 62-mm-Vorlage erscheint also nicht, solange ein
38-mm-Drucker aktiv ist.

Technische Details für Entwickler und KI-Agenten: [AGENTS.md](AGENTS.md).

**So kommen Vorlagen in die App:**

1. Dieses Repository ist in die App eingebunden und wird mit jeder App-Version ausgeliefert.
2. Zusätzlich kann die App einen **Vorlagen-Ordner** aus ihren Einstellungen lesen, z. B. einen
   Klon dieses Repositorys auf einem Netzlaufwerk. Eine Datei dort mit **gleichem Namen**
   ersetzt die eingebaute Vorlage, neue Namen kommen dazu – Änderungen wirken so sofort,
   ohne neue App-Version.

**Prüfen:** Bei jedem Push prüft GitHub Actions alle Vorlagen (`tools/check_templates.py`:
gültiges SVG, Metadaten, mm-Angaben, Jinja-Syntax, nur bekannte Platzhalter). Lokal:
`pip install jinja2 && python tools/check_templates.py`.

## Aufbau

```xml
<svg xmlns="http://www.w3.org/2000/svg" width="80mm" height="62mm" viewBox="0 0 80 62">
  <metadata id="label" data-name="Lagerboxen" data-roll="62" data-length="80"
            data-inputs="sn:Seriennummer"
            data-description="kurze Beschreibung"/>
  <text x="5" y="9" font-size="4.94" font-weight="bold">{{ part_no }}</text>
  <text x="5" y="37" font-size="4.94">{% if po %}PO_{{ po }}{% endif %}</text>
</svg>
```

- **Grösse in mm** (`width`/`height`), am einfachsten mit `viewBox` in mm, dann sind alle
  Koordinaten und Schriftgrössen in mm (Arial 14 pt = 4.94 mm).
- `data-roll`: Breite der Rolle in mm (62, 38, …). Ist die Höhe gleich der Rollenbreite, läuft
  der Text entlang des Bands (Querformat) – die Länge ist dann die Breite des SVG.
- `data-inputs`: Werte, die es in ferp nicht gibt und beim Einbuchen eingetippt werden,
  als `variable:Beschriftung`, mehrere mit `;` getrennt. Leer gelassen sind sie `""`.
- Ränder: quer zum Band sind ca. 1.5 mm, in Laufrichtung ca. 3 mm am Anfang und Ende nicht
  bedruckbar – dort nichts Wichtiges platzieren.
- Erlaubt sind normale SVG-Elemente (Text, Linien, Rechtecke, eingebettete Bilder als
  `data:image/png;base64,…`). Mit Inkscape bearbeitete Dateien funktionieren
  (`<tspan>`, `style="…"`, einfache `transform`).
- **Schrift**: gedruckt wird immer mit der mitgelieferten *Liberation Sans* (gleiche Laufweite
  wie Arial). Eine angegebene `font-family` wird darauf abgebildet. `font-weight="bold"`,
  `font-style="italic"`, `text-anchor="start|middle|end"` werden unterstützt.
- Mehrere Leerzeichen werden wie in jedem SVG zu einem zusammengefasst – Spalten deshalb
  als eigene `<text>`-Elemente mit eigenem `x` setzen.

## Platzhalter

Sprache: [Jinja](https://jinja.palletsprojects.com/) – `{{ name }}` setzt einen Wert ein,
`{% if … %}…{% endif %}` macht etwas bedingt, z. B.
`{% if not uhv %}not clean{% endif %}` oder `{{ length or "______" }}` (Strich, wenn leer).
Ein **unbekannter** Platzhalter (Tippfehler) wird als Fehler in der Vorschau angezeigt statt
leer gedruckt.

| Platzhalter | Inhalt |
|---|---|
| `{{ part_no }}` | Artikelnummer wie in ferp angezeigt, inkl. Variante (z. B. 23337-0130-0006) |
| `{{ part_code }}` | Basis-Artikelnummer ohne Variante (z. B. 23337) |
| `{{ title }}` | Bezeichnung des Artikels |
| `{{ group }}` | Produktgruppe |
| `{{ po }}` | Bestellnummer (O-ID) – die älteste offene Bestellung dieser Position |
| `{{ pos }}` | alle offenen Bestellnummern, mit Komma getrennt |
| `{{ aid }}` | Montage (A-ID), für die die Teile reserviert sind – die älteste |
| `{{ aids }}` | alle Montagen, mit Komma getrennt |
| `{{ uhv }}` | wahr, wenn ferp den Artikel für die Standard-UHV-Reinigung markiert |
| `{{ rev }}` | Revision des Artikels (leer, falls keine oder nicht lesbar) |
| `{{ material }}` | Material |
| `{{ supplier }}` | Lieferant |
| `{{ foreign_code }}` | Artikelnummer des Lieferanten |
| `{{ quantity }}` | eingebuchte Menge |
| `{{ date }}` | Datum des Drucks (TT.MM.JJJJ) |
| `{{ user }}` | angemeldeter ferp-Benutzer |

Dazu alle Eingabefelder aus `data-inputs` unter ihrem Variablennamen.

## Vorhandene Vorlagen

| Datei | Rolle | Herkunft |
|---|---|---|
| `lagerboxen-62.svg` | 62 × 80 mm | 1:1 aus „Wareneingangslabel für Lagerboxen.lbx“ (Teilenummer 2× – wird über die Kante geklebt) |
| `bus-tus-38.svg` | 38 × 98 mm | aus „Wareneingangslabel für BUs und TUs.lbx“, Länge L und SN als Eingabe, „Geprüft“ zum Ausfüllen von Hand |
