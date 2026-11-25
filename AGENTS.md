# AGENTS.md – working on the label templates

This repository holds the **goods-receipt label templates** of the Ferrovac *Wareneingang*
desktop app. Each `*.svg` file in the repository root is one label. The app (a separate,
private repository) fills a template with the data of the item being booked in, shows a
preview and prints it on a Brother QL label printer. This file explains what the app does
with a template, so that changes here print the way they look.

**This repository is public.** Never put confidential data (prices, customer names,
internal hostnames, credentials) into a template — templates only contain layout and
placeholders; the values come from the app at print time.

## How a template gets to the printer

1. **Discovery.** The app loads every top-level `*.svg` (sub-folders are ignored). The file
   name without `.svg` is the template's **id** (e.g. `lagerboxen-62`). Sources, later ones
   override earlier ones by id:
   1. templates built into the app (this repository, as a git submodule, at build time),
   2. this repository downloaded at app start / on "Neu laden" in the booking dialog
      (`https://codeload.github.com/<owner>/<repo>/zip/HEAD`, i.e. the default branch;
      cached locally, so it also works offline; the repository is configurable in the
      app's settings, default `ferrovac/wareneingang-label-templates`),
   3. an optional local folder from the app's settings ("Lokaler Ordner (Test)") — use it to
      try a template before pushing.
   File names may only contain `A-Z a-z 0-9 . _ - space`. Archives over 5 MB are refused.
   Don't rename a template casually: the app remembers the last used id.

2. **Metadata.** Read from the raw file (before filling in values):
   ```xml
   <svg xmlns="http://www.w3.org/2000/svg" width="80mm" height="62mm" viewBox="0 0 80 62">
     <metadata id="label" data-name="Lagerboxen" data-roll="62" data-length="80"
               data-inputs="sn:Seriennummer;length:Länge L (mm)"
               data-description="short description"/>
   ```
   - `width`/`height` **must be in mm**. Use a `viewBox` in mm too, then every coordinate
     and font size is in mm (Arial/Liberation 14 pt = 4.94 mm).
   - `data-roll`: tape width in mm; must equal `width` or `height`. If `height` equals the
     roll, the label is landscape: text runs along the tape and the label length is `width`.
   - `data-inputs`: values ferp doesn't have, typed in by the user when booking:
     `variable:Label`, separated by `;`. Variable names `[a-z_][a-z0-9_]*`, must not shadow a
     built-in placeholder. An empty input is the empty string.

3. **A printer with the matching roll must be active.** The booking dialog only offers
   templates whose `data-roll` matches (±0.5 mm) the roll **reported by the active printer**
   (the one marked "AKTIV" via "Auswählen" in the app; the roll is read over SNMP from the
   printer, e.g. `62mm / 2.4"`). A 62 mm template is invisible while a 38 mm printer is
   selected, and with no active printer nothing can be printed. The roll width must also be
   one `brother_ql` knows for endless tape (12, 18, 29, 38, 50, 54, 62, 102, 103, 104 mm).

4. **Placeholders** (Jinja, rendered over the **whole file**, so they work in text and in
   attributes). The environment is sandboxed, values are **XML-escaped**, and an **unknown
   placeholder is an error** (shown in the preview; nothing is printed) — never print a
   typo silently.

5. **Fonts.** Every `font-family` (attribute or `style`) is replaced by the bundled
   **Liberation Sans** (metric-compatible with Arial, Regular + Bold). Use `font-weight` for
   bold; other families have no effect.

6. **Text is drawn by the app, not by the SVG renderer.** (Qt's SVG text path segfaulted on
   some glyph/size combinations at label scale.) Supported on `<text>` and `<tspan>`:
   `x`, `y` (baseline), `font-size` (a number in user units; a `px`/`mm` suffix is ignored),
   `font-weight` (`bold`, `bolder`, ≥ 600), `font-style` (`italic`/`oblique`),
   `text-anchor` (`start`/`middle`/`end`), `fill`, inheritance of these from ancestor
   `<g>`s (attributes and `style="…"`), and `transform` (`matrix`, `translate`, `scale`,
   `rotate`) on the text and its ancestors. Each `<tspan>` (Inkscape's lines) is drawn on its
   own with its own `x`/`y`/style.
   **Not supported:** `dx`/`dy`, lists of `x` positions, `letter-spacing`, `textLength`,
   `<textPath>`, baseline shifts, `<style>` sheets / CSS classes, `xml:space="preserve"`.
   **Whitespace is always collapsed** (as in any SVG): build columns from separate
   `<text>` elements with their own `x`, not from runs of spaces.

7. **Everything else** (lines, rects, paths, circles, embedded images) is rendered by QtSvg
   (SVG Tiny 1.2 level). Images must be **embedded** (`href="data:image/png;base64,…"`;
   no external files or URLs). The printers are black and white: keep everything pure black
   on white — the bitmap is thresholded at 70 % without dithering, so greys either vanish
   or turn black.

8. **Raster for the printer.** 300 dpi on a white canvas; a landscape template is rotated
   90°; the tape-width axis is fitted to the roll's dots and then **cropped to the printable
   width, centred** (62 mm: 732 → 696 dots, ≈ 1.5 mm lost on each edge; 38 mm: 449 → 413);
   in feed direction the printer's own blank margin (35 dots ≈ 3 mm) is **cut from both ends**
   of the bitmap because the printer adds it back, so the printed label is about as long as
   the template. **Keep content ≥ 2 mm from the long edges and ≥ 3.5 mm from the start/end.**
   The label is cut after each copy; the user picks the number of copies (default 1).

## Placeholders

| Placeholder | Content | Where it comes from |
|---|---|---|
| `part_no` | part number as ferp shows it, incl. variant, e.g. `23337-0130-0006` | ferp Incoming list (ferp's obsolete marker `[` removed) |
| `part_code` | base part number, e.g. `23337` | ferp Incoming list |
| `title` | part title | ferp |
| `group` | product group letter | ferp |
| `po` | purchase order number (O-ID) — the **oldest** open order of this position | ferp (`PO` document; ferp serves deliveries oldest order first) |
| `pos` | all open order numbers, comma-separated | ferp |
| `aid` | assembly (A-ID) the parts are reserved for — the oldest | ferp |
| `aids` | all assemblies, comma-separated | ferp |
| `uhv` | `true` if ferp marks the part for the standard UHV cleaning process | ferp (blue dashed material in ferp) |
| `rev` | part revision, e.g. `A`; **may be empty** (part has none, or the user's ferp group can't open the part page) | ferp part page |
| `material` | material | ferp |
| `supplier` | supplier (ferp contact) | ferp |
| `foreign_code` | the supplier's article number | ferp |
| `quantity` | quantity booked in | booking dialog |
| `date` | print date, `DD.MM.YYYY` | app |
| `user` | the ferp user who is signed in | app |

Plus every variable from `data-inputs`.

Useful Jinja: `{% if not uhv %}not clean{% endif %}`, `{% if rev %}Rev. {{ rev }}{% endif %}`,
`{{ length or "______" }}` (a blank line to fill in by hand when empty),
`{{ title | truncate(30) }}` (shorten long titles).

## Working on templates

- Edit with Inkscape (document units mm) or as plain text. Keep the `metadata` element.
- Run the checker before pushing (CI runs it on every push and pull request):
  ```sh
  pip install "jinja2>=3.1"
  python tools/check_templates.py
  ```
  It checks: valid XML, mm sizes, metadata (`data-name`, `data-roll` matching a side,
  `data-inputs` syntax), Jinja syntax, only known placeholders, and that the file is still
  valid SVG after filling in example values. It does **not** render; check the look in the
  app's preview (local test folder, or push and press "Neu laden").
- Keep `tools/check_templates.py`'s `KNOWN` list, the table above and the app's
  `wareneingang/labels/context.py` (`VARIABLES`) in sync when placeholders change.
- New template: copy the closest one, name it `<name>-<roll>.svg`, set `data-name` and
  `data-roll`, and keep the margins above.
- The original P-touch layouts these came from: `lagerboxen-62.svg` ←
  "Wareneingangslabel für Lagerboxen.lbx", `bus-tus-38.svg` ← "Wareneingangslabel für BUs und
  TUs.lbx" (positions converted from pt to mm 1:1).
