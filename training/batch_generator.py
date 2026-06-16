"""
Batch Generator — erzeugt viele verschiedene synthetische Firmen + Bescheide
und trainiert den Auflagenkatalog über Nacht.

Verwendung:
  py batch_generator.py              → 50 Firmen (Standard)
  py batch_generator.py --firmen 10  → 10 Firmen (Schnelltest)
  py batch_generator.py --dry-run    → Nur generieren, kein API-Call
"""

import json
import random
import os
import sys
import time
import argparse
from pathlib import Path
from datetime import datetime, date, timedelta

# reportlab für PDF-Erzeugung
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
except ImportError:
    print("FEHLER: reportlab fehlt → py -m pip install reportlab")
    sys.exit(1)

BASE = Path(__file__).parent
ROOT = BASE.parent
KATALOG_FILE = ROOT / "synthetic_generator" / "auflagen_katalog.json"
CONFIG_FILE  = ROOT / "dashboard" / "config.json"

OUTPUT_BASE  = BASE / "output"
OUTPUT_BASE.mkdir(exist_ok=True)

random.seed()  # echter Zufall (kein fixer Seed)


# ── Hilfsdaten ─────────────────────────────────────────────────────────────

FIRMENNAMEN = [
    ("AquaNet", "Infrastruktur GmbH"), ("Donau", "Bau AG"), ("Alpine", "Projekt GmbH"),
    ("Enns", "Wasserwirtschaft GmbH"), ("Traun", "Infrastruktur KG"), ("March", "Bau GmbH"),
    ("Inn", "Energie AG"), ("Mur", "Straßenbau GmbH"), ("Salzach", "Netze GmbH"),
    ("Leitha", "Infrastruktur GmbH"), ("Raab", "Bau AG"), ("Ybbs", "Kommunal GmbH"),
    ("Kamp", "Wasser GmbH"), ("Pielach", "Bau KG"), ("Erlauf", "Netze AG"),
    ("Schwechat", "Infrastruktur GmbH"), ("Fischa", "Bau GmbH"), ("Triesting", "Wasser AG"),
    ("Piesting", "Kommunal GmbH"), ("Schwarza", "Infrastruktur KG"),
    ("Mühl", "Bau AG"), ("Aist", "Wasser GmbH"), ("Naarn", "Infrastruktur GmbH"),
    ("Steyr", "Bau AG"), ("Krems", "Netze GmbH"), ("Ager", "Infrastruktur GmbH"),
    ("Vöckla", "Bau GmbH"), ("Mattig", "Wasser KG"), ("Antiesen", "Bau AG"),
    ("Gurk", "Infrastruktur GmbH"), ("Glan", "Bau AG"), ("Lavant", "Netze GmbH"),
    ("Drau", "Infrastruktur AG"), ("Isel", "Bau GmbH"), ("Gail", "Wasser GmbH"),
    ("Lieser", "Infrastruktur KG"), ("Metnitz", "Bau GmbH"), ("Friesach", "Netze AG"),
    ("Semmering", "Infrastruktur GmbH"), ("Schneeberg", "Bau AG"),
    ("Wechsel", "Wasser GmbH"), ("Fischbach", "Infrastruktur KG"),
    ("Lafnitz", "Bau GmbH"), ("Rabnitz", "Netze AG"), ("Zöbern", "Infrastruktur GmbH"),
    ("Pinka", "Bau AG"), ("Strem", "Wasser GmbH"), ("Güns", "Infrastruktur GmbH"),
    ("Ikva", "Bau KG"), ("Wulka", "Netze AG")
]

AUFLAGEN_TEMPLATES = {
    "WRG": [
        ("Ölbindemittel", "Auf der Baustelle sind stets ausreichende Mengen an Ölbindemitteln (mind. {menge} kg) bereitzuhalten und in einem verschlossenen Behälter zu lagern."),
        ("Baustellensicherung", "Die Baustelle ist gemäß § 90 StVO ordnungsgemäß abzusichern. Während der Bauzeit ist eine Verkehrssicherung sicherzustellen."),
        ("Erdarbeiten Protokoll", "Über sämtliche Erdarbeiten im Gewässerbereich ist ein lückenloses Bautagebuch zu führen und der Behörde auf Verlangen vorzulegen."),
        ("Uferböschung wiederherstellen", "Nach Abschluss der Bauarbeiten sind alle Uferböschungen und Dammkronen fachgerecht mit standortgerechten Gehölzen wiederherzustellen."),
        ("Schutzstreifen", "Entlang der Gewässerufer ist ein Schutzstreifen von mindestens {breite} Metern Breite von Bebauung freizuhalten."),
        ("Wassermengenmonitoring", "Die entnommene Wassermenge ist kontinuierlich zu messen. Die maximale Entnahmemenge beträgt {menge} m3/Tag. Aufzeichnungen sind im Betriebsbuch zu führen."),
        ("pH-Wert", "Der pH-Wert des eingeleiteten Wassers ist {intervall} zu messen. Der Grenzwert beträgt 6,5 – 8,5 pH. Die Messergebnisse sind im Probenahmeübersichtsplan zu dokumentieren."),
        ("Sauerstoffgehalt", "Der Sauerstoffgehalt im Ablauf ist monatlich zu messen. Der Mindestwert beträgt {grenzwert} mg/l O2. Bei Unterschreitung ist unverzüglich die Behörde zu informieren."),
        ("Trübung", "Die Trübung des Abwassers ist nach Regenereignissen zu kontrollieren. Grenzwert: {grenzwert} NTU. Ergebnisse sind im Betriebsbuch einzutragen."),
        ("Inspektion Bauwerke", "Alle Einlauf- und Auslaufbauwerke sind {intervall} auf Schäden und Funktionsfähigkeit zu inspizieren. Das Inspektionsprotokoll ist zu hinterlegen."),
        ("GIS-Einmessung", "Sämtliche neu errichteten Bauwerke sind nach Fertigstellung im Koordinatensystem ETRS89/UTM einzumessen und im GIS-System zu erfassen."),
        ("Ökologische Begleitmaßnahmen", "Während der Bauphase ist eine ökologische Baubegleitung durch einen qualifizierten Ökologen sicherzustellen. Protokolle sind vierteljährlich zu dokumentieren."),
        ("Amphibienschutz", "Im Bereich der Laichgewässer (km {von} – km {bis}) sind zwischen 1. März und 31. Mai keine Erdarbeiten durchzuführen. Ausnahmen bedürfen behördlicher Genehmigung."),
        ("Betriebsbuch", "Über alle Betriebsvorgänge ist ein Betriebsbuch zu führen. Sämtliche Wartungs- und Kontrollmaßnahmen sind lückenlos zu dokumentieren."),
        ("§134 Überprüfung", "Die Anlage ist gemäß § 134 WRG einer periodischen Überprüfung zu unterziehen. Die nächste Überprüfung hat bis {datum} zu erfolgen."),
        ("Sedimenträumung", "Das Rückhaltebecken ist bei Bedarf, mindestens jedoch alle {jahre} Jahre zu räumen. Der Sedimentaushub ist ordnungsgemäß zu entsorgen."),
        ("Mahd", "Die Böschungen sind mindestens {anzahl}x jährlich zu mähen. Das Mähgut ist abzutragen und einer geordneten Entsorgung zuzuführen."),
        ("Neophyten", "Invasive Neophyten (insbesondere Japanknöterich, Drüsiges Springkraut) sind unverzüglich nach Auftreten fachgerecht zu entfernen."),
        ("Zink messen", "Der Parameter Zink ist jährlich im Ablauf des Rückhaltebeckens zu messen. Grenzwert: {grenzwert} mg/l gemäß ÖNORM EN ISO 11885."),
        ("KW-Index", "Der KW-Index ist halbjährlich im Ablauf zu messen. Grenzwert: {grenzwert} mg/l gemäß ÖNORM EN ISO 9377-2."),
    ],
    "BAU": [
        ("Brandschutz", "Die Brandschutzanlage ist gemäß OIB-Richtlinie 2 auszuführen. Ein Brandschutzplan ist vor Baubeginn der Behörde vorzulegen."),
        ("Stellplätze", "Es sind mindestens {anzahl} KFZ-Stellplätze gemäß Wiener Garagengesetz herzustellen."),
        ("Lärmschutz Bau", "Während der Bauphase sind die zulässigen Schallpegel gemäß ÖNORM B 8115 einzuhalten. Bauarbeiten sind werktags von 7:00 bis 19:00 Uhr beschränkt."),
        ("Entwässerung", "Das anfallende Niederschlagswasser ist über eine Sickeranlage bzw. Retentionsbecken zu versickern. Direkteinleitung ist nicht zulässig."),
        ("Abstandsflächen", "Die Abstandsflächen gemäß § 79 WBO sind mit mindestens {meter} Metern einzuhalten."),
        ("Benützungsbewilligung", "Vor Inbetriebnahme des Gebäudes ist eine Benützungsbewilligung bei der Baubehörde zu beantragen."),
        ("Energieausweis", "Ein Energieausweis gemäß OIB-Richtlinie 6 ist vor Fertigstellung vorzulegen."),
        ("Barrierefreiheit", "Das Gebäude ist gemäß ÖNORM B 1600 barrierefrei zu gestalten."),
    ],
    "UVP": [
        ("Lärmmessung", "Die Lärmimmissionen sind während der Bauphase monatlich zu messen. Grenzwert: {grenzwert} dB(A) tags."),
        ("Grundwassermonitoring", "Das Grundwasser ist im Bereich der Baumaßnahme vierteljährlich auf Lage und Qualität zu überwachen."),
        ("Flora-Fauna-Monitoring", "Ein jährliches Monitoring der betroffenen Flora- und Fauna-Habitate ist durchzuführen. Ergebnisse sind dem BMKLIMA zu berichten."),
        ("Erschütterungen", "Erschütterungen während der Bauphase sind kontinuierlich zu messen. Grenzwert: {grenzwert} mm/s Schwinggeschwindigkeit."),
        ("Ausgleichsflächen", "Für beeinträchtigte Lebensräume sind Ausgleichsflächen im Ausmaß von {faktor}:1 anzulegen."),
        ("Beweissicherung", "Vor Baubeginn ist eine Beweissicherung der angrenzenden Gebäude durch einen Ziviltechniker durchzuführen."),
        ("Staubemissionen", "Zur Vermeidung von Staubemissionen sind Befeuchtungsmaßnahmen durchzuführen. PM10-Grenzwert: {grenzwert} µg/m3."),
    ],
    "STR": [
        ("Lärmschutzwand", "Eine Lärmschutzwand mit einer Höhe von mindestens {hoehe} m ist entlang der Trasse km {von} bis km {bis} zu errichten."),
        ("Wildquerung", "Im Bereich km {km} ist eine Wildquerung gemäß Leitfaden Wildquerungen zu errichten."),
        ("Entwässerung Straße", "Das Straßenoberflächenwasser ist über Mulden und Retentionsbecken zu behandeln. Direkteinleitung in Gewässer ist unzulässig."),
        ("Bepflanzung", "Der Straßendamm ist mit standortgerechten Gehölzen zu bepflanzen. Ein Bepflanzungsplan ist vor Baubeginn vorzulegen."),
        ("Beleuchtung", "Die Straßenbeleuchtung ist mit energieeffizienten LED-Leuchten auszuführen."),
    ]
}

def weighted_choice(choices):
    items = [c["id"] for c in choices]
    weights = [c["gewicht"] for c in choices]
    return random.choices(items, weights=weights, k=1)[0]

def generate_firma(idx, config):
    name_prefix, name_suffix = FIRMENNAMEN[idx % len(FIRMENNAMEN)]
    firmentyp = random.choice(config["firmentypen"])
    domänen_config = config["domänen"]
    domäne_id = weighted_choice(domänen_config)
    domäne = next(d for d in domänen_config if d["id"] == domäne_id)

    mitarbeiter = random.randint(*firmentyp["mitarbeiter_range"])
    return {
        "firma_id": f"FIRM-{idx+1:04d}",
        "name": f"{name_prefix} {name_suffix}",
        "typ": firmentyp["typ"],
        "domäne": domäne_id,
        "domäne_name": domäne["name"],
        "mitarbeiter": mitarbeiter,
        "hauptsitz": random.choice(["Wien", "Linz", "Graz", "Salzburg", "Innsbruck", "St. Pölten", "Eisenstadt"]),
        "behoerden": domäne["behoerden"],
        "bescheidarten": domäne["bescheidarten"],
        "auflagen_themen": domäne["auflagen_themen"],
        "domäne_config": domäne
    }

def generate_bescheid_text(firma, bescheid_nr, domäne_id):
    bescheidart = random.choice(firma["bescheidarten"])
    behoerde = random.choice(firma["behoerden"])
    gz_nr = random.randint(10000, 99999)
    gz_sub = random.randint(100, 999)

    prefix = {"WRG": "WA1-W", "BAU": "BA", "UVP": "UVP", "STR": "STR"}.get(domäne_id, "GZ")
    gz = f"{prefix}-{gz_nr}/{gz_sub:03d}"

    jahr = random.randint(1985, 2024)
    monat = random.randint(1, 12)
    tag = random.randint(1, 28)
    datum = f"{tag:02d}. {['Jänner','Februar','März','April','Mai','Juni','Juli','August','September','Oktober','November','Dezember'][monat-1]} {jahr}"

    # Auflagen für diese Domäne auswählen (5-12 Stück)
    templates = AUFLAGEN_TEMPLATES.get(domäne_id, AUFLAGEN_TEMPLATES["WRG"])
    n_auflagen = random.randint(5, min(12, len(templates)))
    selected = random.sample(templates, n_auflagen)

    # Parameter einsetzen
    def fill(text):
        return (text
            .replace("{menge}", str(random.randint(20, 200)))
            .replace("{breite}", str(random.randint(3, 10)))
            .replace("{grenzwert}", str(round(random.uniform(0.1, 20.0), 1)))
            .replace("{intervall}", random.choice(["wöchentlich", "monatlich", "vierteljährlich", "halbjährlich"]))
            .replace("{von}", str(round(random.uniform(0, 50), 1)))
            .replace("{bis}", str(round(random.uniform(51, 100), 1)))
            .replace("{datum}", f"31. Dezember {random.randint(2025, 2035)}"))  \
            .replace("{jahre}", str(random.randint(2, 10))) \
            .replace("{anzahl}", str(random.randint(1, 4))) \
            .replace("{faktor}", str(random.randint(1, 3))) \
            .replace("{hoehe}", str(random.randint(2, 6))) \
            .replace("{km}", str(round(random.uniform(0, 100), 1))) \
            .replace("{meter}", str(random.randint(3, 6)))

    auflagen = [(titel, fill(text)) for titel, text in selected]
    return gz, bescheidart, behoerde, datum, auflagen

def create_pdf(firma, bescheid_nr, gz, bescheidart, behoerde, datum, auflagen, out_dir):
    pdf_path = out_dir / f"bescheid_{bescheid_nr:02d}_{gz.replace('/','-').replace(' ','-')}.pdf"

    styles = getSampleStyleSheet()
    normal = styles["Normal"]
    normal.fontName = "Helvetica"; normal.fontSize = 10; normal.leading = 14
    center = ParagraphStyle("c", parent=normal, alignment=1)
    h1 = ParagraphStyle("h1", parent=normal, fontSize=13, fontName="Helvetica-Bold", spaceAfter=6, spaceBefore=12)
    h2 = ParagraphStyle("h2", parent=normal, fontSize=11, fontName="Helvetica-Bold", spaceAfter=4, spaceBefore=8)
    bold = ParagraphStyle("b", parent=normal, fontName="Helvetica-Bold")

    doc = SimpleDocTemplate(str(pdf_path), pagesize=A4,
                            topMargin=2.5*cm, bottomMargin=2.5*cm,
                            leftMargin=2.5*cm, rightMargin=2.5*cm)
    story = []
    story.append(Paragraph(behoerde.upper(), center))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("BESCHEID", ParagraphStyle("t", parent=center, fontSize=16, fontName="Helvetica-Bold")))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(f"GZ: {gz}", bold))
    story.append(Paragraph(f"Datum: {datum}", normal))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(f"Antragstellerin: {firma['name']}, {firma['hauptsitz']}", normal))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        f"Die Behörde erteilt der {firma['name']} gemäß den einschlägigen gesetzlichen Bestimmungen "
        f"die {bescheidart} für die beantragte Maßnahme unter folgenden Auflagen:", normal))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("AUFLAGEN UND BEDINGUNGEN", h1))

    for i, (titel, text) in enumerate(auflagen, 1):
        story.append(Paragraph(f"<b>{i}. {titel}:</b>", normal))
        story.append(Paragraph(text, normal))
        story.append(Spacer(1, 0.15*cm))

    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("RECHTSMITTELBELEHRUNG", h2))
    story.append(Paragraph("Gegen diesen Bescheid kann innerhalb von vier Wochen ab Zustellung Beschwerde erhoben werden.", normal))

    doc.build(story)
    return pdf_path

def process_with_claude(pdf_path, katalog, api_key):
    import anthropic
    sys.path.insert(0, str(ROOT / "modul1"))
    import bescheid_processor as bp
    import importlib; importlib.reload(bp)
    os.environ["ANTHROPIC_API_KEY"] = api_key
    pdf_text = bp.extract_pdf_text(str(pdf_path))
    return bp.classify_with_claude(pdf_text, katalog)

def run_batch(firmen_anzahl, dry_run=False, bescheide_pro_firma=8):
    print(f"\n{'='*65}")
    print(f"  BATCH GENERATOR — {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    print(f"  Firmen: {firmen_anzahl} | Bescheide/Firma: {bescheide_pro_firma} | Dry-Run: {dry_run}")
    print(f"{'='*65}\n")

    with open(BASE / "batch_config.json", encoding="utf-8") as f:
        config = json.load(f)

    with open(KATALOG_FILE, encoding="utf-8") as f:
        katalog_data = json.load(f)
    katalog = katalog_data["katalog"]

    api_key = ""
    if not dry_run:
        if os.environ.get("ANTHROPIC_API_KEY"):
            api_key = os.environ["ANTHROPIC_API_KEY"]
        else:
            cfg_file = ROOT / "dashboard" / "config.json"
            if cfg_file.exists():
                with open(cfg_file, encoding="utf-8") as f:
                    api_key = json.load(f).get("anthropic_api_key", "")
        if not api_key:
            print("FEHLER: Kein API-Key. Setze $env:ANTHROPIC_API_KEY oder speichere in Einstellungen.")
            sys.exit(1)

    # Ausgabe-Verzeichnis für diesen Lauf
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = OUTPUT_BASE / run_id
    run_dir.mkdir(parents=True)

    gesamtergebnis = {
        "run_id": run_id,
        "gestartet": datetime.now().isoformat(),
        "firmen": [],
        "aggregiert": {
            "total_bescheide": 0,
            "total_auflagen": 0,
            "total_auto": 0,
            "total_pruefung": 0,
            "total_manuell": 0,
            "total_nicht_zuordenbar": 0,
            "kosten_usd": 0.0,
            "nicht_zuordenbar_texte": [],
            "konfidenz_verteilung": {}
        }
    }

    for i in range(firmen_anzahl):
        firma = generate_firma(i, config)
        firma_dir = run_dir / firma["firma_id"]
        firma_dir.mkdir()

        print(f"[{i+1:3d}/{firmen_anzahl}] {firma['name']:<35} | {firma['domäne_name']:<20}", end="", flush=True)

        firma_ergebnis = {
            "firma": {k: v for k, v in firma.items() if k != "domäne_config"},
            "bescheide": []
        }

        for b in range(bescheide_pro_firma):
            gz, bescheidart, behoerde, datum, auflagen = generate_bescheid_text(firma, b+1, firma["domäne"])
            pdf_path = create_pdf(firma, b+1, gz, bescheidart, behoerde, datum, auflagen, firma_dir)

            bescheid_result = {
                "gz": gz, "art": bescheidart, "auflagen_count": len(auflagen),
                "pdf": pdf_path.name
            }

            if not dry_run:
                try:
                    result = process_with_claude(pdf_path, katalog, api_key)
                    auflagen_r = result.get("auflagen", [])
                    nicht_r    = result.get("nicht_zuordenbar", [])
                    api_info   = result.get("api_info", {})

                    auto     = sum(1 for a in auflagen_r if a.get("konfidenz", 0) >= 0.90)
                    pruefung = sum(1 for a in auflagen_r if 0.70 <= a.get("konfidenz", 0) < 0.90)
                    manuell  = sum(1 for a in auflagen_r if a.get("konfidenz", 0) < 0.70)

                    bescheid_result.update({
                        "ki_auflagen": len(auflagen_r),
                        "auto": auto, "pruefung": pruefung, "manuell": manuell,
                        "nicht_zuordenbar": len(nicht_r),
                        "kosten_usd": api_info.get("geschaetzte_kosten_usd", 0)
                    })

                    # Aggregieren
                    agg = gesamtergebnis["aggregiert"]
                    agg["total_bescheide"] += 1
                    agg["total_auflagen"] += len(auflagen_r)
                    agg["total_auto"] += auto
                    agg["total_pruefung"] += pruefung
                    agg["total_manuell"] += manuell
                    agg["total_nicht_zuordenbar"] += len(nicht_r)
                    agg["kosten_usd"] += api_info.get("geschaetzte_kosten_usd", 0)
                    for n in nicht_r:
                        agg["nicht_zuordenbar_texte"].append({
                            "firma": firma["name"],
                            "domäne": firma["domäne"],
                            "text": n.get("originaltext", "")[:100],
                            "grund": n.get("grund", "")
                        })

                    # Kostenlimit prüfen
                    if agg["kosten_usd"] >= config["max_kosten_usd"]:
                        print(f"\n  KOSTENLIMIT ${config['max_kosten_usd']} erreicht — stoppe.")
                        break

                    time.sleep(0.5)  # Rate-Limit-Puffer

                except Exception as e:
                    bescheid_result["fehler"] = str(e)

            firma_ergebnis["bescheide"].append(bescheid_result)

        gesamtergebnis["firmen"].append(firma_ergebnis)
        status = "OK (dry)" if dry_run else f"OK ${gesamtergebnis['aggregiert']['kosten_usd']:.4f}"
        print(f" {status}")

    # Ergebnis speichern
    gesamtergebnis["aggregiert"]["kosten_usd"] = round(gesamtergebnis["aggregiert"]["kosten_usd"], 4)
    result_file = run_dir / "batch_ergebnis.json"
    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(gesamtergebnis, f, ensure_ascii=False, indent=2)

    # Katalog-Kandidaten ableiten
    if not dry_run:
        _print_katalog_empfehlungen(gesamtergebnis, run_dir)

    print(f"\n{'='*65}")
    agg = gesamtergebnis["aggregiert"]
    if not dry_run:
        total = agg["total_auto"] + agg["total_pruefung"] + agg["total_manuell"]
        auto_rate = round(agg["total_auto"] / total * 100, 1) if total > 0 else 0
        print(f"  Bescheide verarbeitet: {agg['total_bescheide']}")
        print(f"  Auflagen analysiert:   {agg['total_auflagen']}")
        print(f"  Auto-Rate:             {auto_rate}%")
        print(f"  Nicht zuordenbar:      {agg['total_nicht_zuordenbar']}")
        print(f"  Gesamtkosten:          ${agg['kosten_usd']:.4f} USD")
    else:
        print(f"  PDFs erzeugt:          {firmen_anzahl * bescheide_pro_firma}")
        print(f"  Dry-Run — kein API-Aufruf")
    print(f"  Output:                {run_dir}")
    print(f"{'='*65}\n")
    return gesamtergebnis

def _print_katalog_empfehlungen(ergebnis, run_dir):
    """Analysiert nicht-zuordenbare Auflagen und schlägt neue Katalog-Einträge vor."""
    nicht_texte = ergebnis["aggregiert"]["nicht_zuordenbar_texte"]
    if not nicht_texte:
        return

    # Nach Domäne gruppieren
    nach_domaene = {}
    for n in nicht_texte:
        d = n.get("domäne", "?")
        nach_domaene.setdefault(d, []).append(n["text"])

    report = {
        "erstellt": datetime.now().isoformat(),
        "total_nicht_zuordenbar": len(nicht_texte),
        "empfehlungen_nach_domaene": nach_domaene,
        "hinweis": "Diese Texte wurden von Claude nicht dem Katalog zugeordnet. Prüfe ob neue Katalog-Einträge sinnvoll sind."
    }

    report_file = run_dir / "katalog_kandidaten.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n  Katalog-Kandidaten gespeichert: {report_file.name}")
    print(f"  Nicht zuordenbar nach Domäne:")
    for d, texte in nach_domaene.items():
        print(f"    {d}: {len(texte)} Auflagen")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch Generator für Auflagenkatalog-Training")
    parser.add_argument("--firmen", type=int, default=50, help="Anzahl synthetischer Firmen")
    parser.add_argument("--bescheide", type=int, default=8, help="Bescheide pro Firma")
    parser.add_argument("--dry-run", action="store_true", help="Nur PDFs erzeugen, kein API-Call")
    args = parser.parse_args()

    run_batch(
        firmen_anzahl=args.firmen,
        bescheide_pro_firma=args.bescheide,
        dry_run=args.dry_run
    )
