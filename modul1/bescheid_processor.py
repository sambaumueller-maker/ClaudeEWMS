"""
Modul 1 — Bescheid Processing Engine
Liest einen Bescheid-PDF, extrahiert Auflagen mit Claude AI,
und ordnet sie dem Auflagenkatalog zu.
"""

import json
import os
import sys
from pathlib import Path
import pdfplumber
import anthropic

BASE = Path(__file__).parent.parent
KATALOG_FILE = BASE / "synthetic_generator" / "auflagen_katalog.json"
OUTPUT_DIR = BASE / "modul1" / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


def load_katalog():
    with open(KATALOG_FILE, encoding="utf-8") as f:
        data = json.load(f)
    return data["katalog"]


def extract_pdf_text(pdf_path: str) -> str:
    text_parts = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            t = page.extract_text()
            if t:
                text_parts.append(f"--- Seite {i+1} ---\n{t}")
    return "\n\n".join(text_parts)


def build_katalog_summary(katalog: list) -> str:
    lines = []
    for k in katalog:
        synonyme = ", ".join(k.get("synonyme", []))
        lines.append(
            f"ID={k['auflagen_id']} | Typ={k['auflagentyp']} | "
            f"Fachbereich={k['fachbereich']} | Zielsystem={k['zielsystem']} | "
            f"Synonyme: {synonyme}"
        )
    return "\n".join(lines)


STRUKTUR_PROMPT = """Du bist Experte für österreichische Verwaltungsbescheide (Wasserrecht, Baurecht, UVP).

Deine Aufgabe: Analysiere den Bescheid-Rohtext und extrahiere NUR den Abschnitt, der tatsächliche
Auflagen, Bedingungen und Vorschreibungen enthält.

WICHTIGE UNTERSCHEIDUNGEN:
- IGNORIEREN: Spruch-Einleitung ("Bezugnehmend auf...", "Aufgrund des Antrages...", Aktenzeichen-Verweise)
- IGNORIEREN: Begründung (erkennbar an "Die Behörde hat erwogen...", "Gemäß § X WRG ist...")
- IGNORIEREN: Rechtsmittelbelehrung ("Gegen diesen Bescheid kann...")
- IGNORIEREN: Verfahrensgeschichte und Sachverhaltsschilderung
- EXTRAHIEREN: Nummerierte oder bezeichnete Auflagen ("1.", "I.", "a)", "Auflage 1:")
- EXTRAHIEREN: Sätze mit Verpflichtungscharakter: "ist zu ...", "sind zu ...", "hat zu ...",
  "wird aufgetragen", "wird vorgeschrieben", "ist sicherzustellen", "ist zu gewährleisten",
  "darf nur ... wenn", "ist verboten", "ist einzuhalten", "ist vorzulegen"
- EXTRAHIEREN: Grenzwerte, Messverpflichtungen, Fristen, Meldepflichten

Antworte NUR mit JSON:
{
  "bescheid_art": "Bewilligungsbescheid|Kollaudierungsbescheid|Änderungsbescheid|Wiederverleihung|Unbekannt",
  "behoerde": "Name der Behörde",
  "gz": "Geschäftszahl z.B. WA1-W-12345/021",
  "datum": "Bescheiddatum",
  "auflagen_abschnitt_gefunden": true,
  "auflagen_rohtext": [
    {
      "nummer": "1.",
      "text": "Vollständiger Auflagentext"
    }
  ],
  "dokument_qualitaet": "gut|mittel|schlecht",
  "hinweis": "Optionaler Hinweis z.B. 'Bescheid aus 1973, sehr langer Fließtext'"
}"""

KLASSIFIKATION_PROMPT = """Du bist Experte für österreichisches Wasserrecht.

Ordne jede extrahierte Auflage dem passenden Eintrag aus dem Auflagenkatalog zu.

AUFLAGENKATALOG:
{katalog}

EXTRAHIERTE AUFLAGEN:
{auflagen_json}

Regeln für die Zuordnung:
- Konfidenz 0.90-1.00: Eindeutiger Match (gleicher Auflagentyp oder Synonym)
- Konfidenz 0.70-0.89: Wahrscheinlicher Match (ähnliche Maßnahme, andere Formulierung)
- Konfidenz 0.50-0.69: Möglicher Match (gleicher Fachbereich, aber abweichend)
- Konfidenz unter 0.50: Kein sinnvoller Match → in "nicht_zuordenbar"

Antworte NUR mit JSON:
{{
  "auflagen": [
    {{
      "nummer": "Auflagennummer aus dem Bescheid",
      "originaltext": "Originaltext (max 200 Zeichen)",
      "katalog_id": "z.B. W001 oder null",
      "katalog_bezeichnung": "Auflagentyp aus Katalog oder null",
      "zielsystem": "Zielsystem oder null",
      "massnahmentyp": "VERM|AUSG|MONI|BEWS|BEGL|EINM|PERI oder null",
      "konfidenz": 0.95,
      "begruendung": "Ein Satz Begründung"
    }}
  ],
  "nicht_zuordenbar": [
    {{
      "nummer": "Auflagennummer",
      "originaltext": "Text",
      "grund": "Warum kein Katalog-Match"
    }}
  ],
  "zusammenfassung": {{
    "auflagen_gesamt": 0,
    "zugeordnet": 0,
    "nicht_zugeordnet": 0,
    "durchschnittliche_konfidenz": 0.0
  }}
}}"""


def extract_struktur(client, pdf_text: str) -> dict:
    """Stufe 1: Dokumentstruktur erkennen und Auflagen-Rohtexte isolieren."""
    pdf_excerpt = pdf_text[:12000]
    if len(pdf_text) > 12000:
        pdf_excerpt += f"\n\n[... {len(pdf_text)-12000} Zeichen gekürzt ...]"

    print("  Stufe 1: Dokumentstruktur analysieren...")
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=3000,
        messages=[{"role": "user", "content": STRUKTUR_PROMPT + f"\n\nBESCHEID-ROHTEXT:\n{pdf_excerpt}"}]
    )
    text = msg.content[0].text
    start = text.find("{"); end = text.rfind("}") + 1
    result = json.loads(text[start:end])
    result["_tokens_stufe1"] = {"input": msg.usage.input_tokens, "output": msg.usage.output_tokens}

    n = len(result.get("auflagen_rohtext", []))
    qualitaet = result.get("dokument_qualitaet", "?")
    hinweis = result.get("hinweis", "")
    print(f"  → {n} Auflagen-Rohtexte gefunden | Qualität: {qualitaet}" + (f" | {hinweis}" if hinweis else ""))
    return result


def classify_with_claude(pdf_text: str, katalog: list) -> dict:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY ist nicht gesetzt. Bitte setzen mit: $env:ANTHROPIC_API_KEY = 'sk-ant-...'")

    client = anthropic.Anthropic(api_key=api_key)
    katalog_summary = build_katalog_summary(katalog)

    # Stufe 1: Struktur + Auflagen-Extraktion
    struktur = extract_struktur(client, pdf_text)
    auflagen_roh = struktur.get("auflagen_rohtext", [])

    if not auflagen_roh:
        return {
            "bescheid_info": {
                "erkannte_art": struktur.get("bescheid_art", "Unbekannt"),
                "behoerde": struktur.get("behoerde"),
                "gz": struktur.get("gz"),
                "datum": struktur.get("datum"),
            },
            "auflagen": [],
            "nicht_zuordenbar": [],
            "zusammenfassung": {"auflagen_gesamt": 0, "zugeordnet": 0, "nicht_zugeordnet": 0, "durchschnittliche_konfidenz": 0},
            "dokument_qualitaet": struktur.get("dokument_qualitaet", "?"),
            "hinweis": struktur.get("hinweis", "Keine Auflagen gefunden"),
            "api_info": {"model": "claude-haiku-4-5-20251001",
                         "input_tokens": struktur["_tokens_stufe1"]["input"],
                         "output_tokens": struktur["_tokens_stufe1"]["output"],
                         "geschaetzte_kosten_usd": 0}
        }

    # Stufe 2: Katalog-Klassifikation
    print(f"  Stufe 2: {len(auflagen_roh)} Auflagen klassifizieren...")
    prompt2 = KLASSIFIKATION_PROMPT.format(
        katalog=katalog_summary,
        auflagen_json=json.dumps(auflagen_roh, ensure_ascii=False, indent=2)
    )
    msg2 = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt2}]
    )
    text2 = msg2.content[0].text
    start = text2.find("{"); end = text2.rfind("}") + 1
    result = json.loads(text2[start:end])

    t1 = struktur["_tokens_stufe1"]
    total_in  = t1["input"]  + msg2.usage.input_tokens
    total_out = t1["output"] + msg2.usage.output_tokens

    result["bescheid_info"] = {
        "erkannte_art": struktur.get("bescheid_art", "Unbekannt"),
        "behoerde": struktur.get("behoerde"),
        "gz": struktur.get("gz"),
        "datum": struktur.get("datum"),
    }
    result["dokument_qualitaet"] = struktur.get("dokument_qualitaet", "?")
    result["hinweis"] = struktur.get("hinweis", "")
    result["api_info"] = {
        "model": "claude-haiku-4-5-20251001",
        "input_tokens": total_in,
        "output_tokens": total_out,
        "geschaetzte_kosten_usd": round((total_in * 0.00000025) + (total_out * 0.00000125), 5)
    }

    print(f"  Stufe 2: Abgeschlossen")
    return result


def print_result(result: dict):
    info = result.get("bescheid_info", {})
    print(f"\n{'='*60}")
    print(f"  BESCHEID-ANALYSE ERGEBNIS")
    print(f"{'='*60}")
    print(f"  Art:      {info.get('erkannte_art', '?')}")
    print(f"  Behoerde: {info.get('behoerde', '?')}")
    print(f"  GZ:       {info.get('gz', '?')}")
    print(f"  Datum:    {info.get('datum', '?')}")
    if result.get("dokument_qualitaet"):
        print(f"  Qualitaet:{result['dokument_qualitaet']}")
    if result.get("hinweis"):
        print(f"  Hinweis:  {result['hinweis']}")

    auflagen = result.get("auflagen", [])
    print(f"\n  Erkannte Auflagen: {len(auflagen)}")

    gruen = [a for a in auflagen if a.get("konfidenz", 0) >= 0.90]
    gelb  = [a for a in auflagen if 0.70 <= a.get("konfidenz", 0) < 0.90]
    rot   = [a for a in auflagen if a.get("konfidenz", 0) < 0.70]

    print(f"  GRUEN (>=0.90): {len(gruen)} — automatisch zuordnen")
    print(f"  GELB  (0.70-0.89): {len(gelb)} — manuelle Pruefung")
    print(f"  ROT   (<0.70): {len(rot)} — manuelle Eingabe")

    print(f"\n  {'Nr.':<8} {'Katalog-ID':<12} {'Konfidenz':<12} {'Zielsystem':<28} {'Originaltext'}")
    print(f"  {'-'*90}")
    for a in auflagen:
        k = a.get("konfidenz", 0)
        farbe = "GRUEN" if k >= 0.90 else ("GELB" if k >= 0.70 else "ROT ")
        text = a.get("originaltext", "")[:45]
        print(f"  [{farbe}] {a.get('nummer','?'):<6} {a.get('katalog_id','?'):<12} {k:<12.2f} {a.get('zielsystem','?'):<28} {text}")

    nicht = result.get("nicht_zuordenbar", [])
    if nicht:
        print(f"\n  Nicht zuordenbar ({len(nicht)}):")
        for n in nicht:
            print(f"    - {n.get('originaltext','')[:60]} → {n.get('grund','')}")

    api = result.get("api_info", {})
    print(f"\n  API-Kosten: ${api.get('geschaetzte_kosten_usd', 0):.5f} USD")
    print(f"  Tokens: {api.get('input_tokens',0)} input / {api.get('output_tokens',0)} output")
    print(f"{'='*60}\n")


def process_bescheid(pdf_path: str):
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        print(f"FEHLER: Datei nicht gefunden: {pdf_path}")
        sys.exit(1)

    print(f"\nModul 1 — Bescheid Processor")
    print(f"Datei: {pdf_path.name}")

    print("  Lade Auflagenkatalog...")
    katalog = load_katalog()
    print(f"  {len(katalog)} Katalog-Eintraege geladen")

    print("  Extrahiere PDF-Text...")
    pdf_text = extract_pdf_text(str(pdf_path))
    print(f"  {len(pdf_text)} Zeichen extrahiert")

    if len(pdf_text) < 100:
        print("  WARNUNG: Sehr wenig Text — PDF ist moeglicherweise gescannt (kein OCR)")

    result = classify_with_claude(pdf_text, katalog)

    output_file = OUTPUT_DIR / f"{pdf_path.stem}_analyse.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"  Ergebnis gespeichert: {output_file}")

    print_result(result)
    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Verwendung: py bescheid_processor.py <pfad_zum_pdf>")
        print("Beispiel:   py bescheid_processor.py C:\\Dokumente\\bescheid.pdf")
        sys.exit(1)

    process_bescheid(sys.argv[1])
