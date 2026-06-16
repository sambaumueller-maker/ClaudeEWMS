"""
Synthetic Company Generator — AquaNet Infrastruktur GmbH
Domäne: Wasserrecht
"""

import json
import csv
import random
import os
from datetime import date, timedelta
from pathlib import Path

random.seed(42)

BASE = Path(__file__).parent
OUT  = BASE / "output"
OUT.mkdir(exist_ok=True)

with open(BASE / "company_definition.json", encoding="utf-8") as f:
    COMPANY = json.load(f)

with open(BASE / "auflagen_katalog.json", encoding="utf-8") as f:
    KATALOG = json.load(f)["katalog"]

KATALOG_MAP = {k["auflagen_id"]: k for k in KATALOG}

BEHOERDEN = [
    "BH Korneuburg", "BH St. Pölten", "MA 45 Wien", "BH Wels-Land",
    "BH Braunau am Inn", "LH Niederösterreich"
]
BESCHEIDARTEN = [
    "Bewilligungsbescheid", "Kollaudierungsbescheid",
    "Änderungsbescheid", "Wiederverleihung"
]
AUSLEITUNGSTYPEN = ["Vorfluter", "Mischform", "Direkteinleitung", "Versickerung"]
ELEMENTTYPEN = [
    "Einlaufbauwerk", "Auslaufbauwerk", "Zulauf", "Einzäunung",
    "Schieber", "Trennbauwerk", "Rückhaltebecken", "Drosselorgan"
]
DOKUMENTTYPEN = [
    "Genehmigungsbescheid", "Kollaudierungsbescheid", "Lageplan",
    "Technischer Bericht", "Laborprotokoll", "Prüfbericht §134"
]

STATUS_BESCHEID = [
    ("Produktiv", 0.60), ("Prüfung offen", 0.15),
    ("In Bearbeitung", 0.15), ("Zurückgewiesen", 0.10)
]

def weighted_choice(choices):
    items, weights = zip(*choices)
    r = random.random()
    cumul = 0
    for item, w in zip(items, weights):
        cumul += w
        if r < cumul:
            return item
    return items[-1]

def rand_date(start_year=2010, end_year=2025):
    start = date(start_year, 1, 1)
    end   = date(end_year, 12, 31)
    return start + timedelta(days=random.randint(0, (end - start).days))

def rand_future_date(years=5, years_max=30):
    today = date.today()
    return today + timedelta(days=random.randint(years * 365, years_max * 365))

def rand_past_date(years=3):
    today = date.today()
    return today - timedelta(days=random.randint(0, years * 365))

def fmt(d):
    return d.strftime("%d.%m.%Y") if d else ""

# ──────────────────────────────────────────────
# 1. BESCHEIDE
# ──────────────────────────────────────────────
def generate_bescheide(n=12):
    rows = []
    strecken = COMPANY["organisation"]["abms"]
    regionen = COMPANY["organisation"]["regionen"]
    netz     = COMPANY["netz"]["strecken"]

    for i in range(1, n + 1):
        strecke  = random.choice(netz)
        abm_list = [a for a in COMPANY["organisation"]["abms"] if a["region"] == strecke["region"]]
        abm      = random.choice(abm_list) if abm_list else random.choice(COMPANY["organisation"]["abms"])
        km_von   = round(random.uniform(0, strecke["km"] - 5), 1)
        km_bis   = round(km_von + random.uniform(1, min(20, strecke["km"] - km_von)), 1)
        bescheid_datum = rand_date(2005, 2023)
        befristung = bescheid_datum + timedelta(days=random.randint(10 * 365, 30 * 365))
        bmg  = next(p for p in COMPANY["organisation"]["personen"] if p["rolle"] == "BMG")
        bum  = next(p for p in COMPANY["organisation"]["personen"] if p["rolle"] == "BUM-E")
        status = weighted_choice(STATUS_BESCHEID)
        bearbeitet = rand_past_date(2) if status != "Prüfung offen" else None

        rows.append({
            "Bescheid_ID":          f"B-{bescheid_datum.strftime('%Y%m%d')}{i:04d}",
            "GZ":                   f"WA1-W-{random.randint(10000,99999)}/{random.randint(100,999)}",
            "Wasserbuch":           f"WB-{1000 + i}",
            "Behörde":              random.choice(BEHOERDEN),
            "Bescheiddatum":        fmt(bescheid_datum),
            "Bescheidart":          random.choice(BESCHEIDARTEN),
            "Region":               strecke["region"],
            "ABM":                  abm["name"],
            "Strecke":              strecke["name"],
            "Abschnitt":            f"A{random.randint(1,9):02d}",
            "km_von":               km_von,
            "km_bis":               km_bis,
            "Befristung_bis":       fmt(befristung),
            "Wiederverleihung":     random.choice(["Ja", "Nein"]),
            "Kollaudierung":        random.choice(["Ja", "Nein"]),
            "§134_erforderlich":    random.choice(["Ja", "Nein"]),
            "Status":               status,
            "Erfasst_von_BMG":      fmt(rand_past_date(3)),
            "BMG_Bearbeiter":       bmg["name"],
            "Freigegeben_von_BUM":  fmt(bearbeitet),
            "BUM_Bearbeiter":       bum["name"] if bearbeitet else "",
            "DOXIS_Link":           f"https://doxis.aquanet.at/bescheide/{1000+i}",
            "Bescheidakte":         f"WA1-W-{random.randint(10000,99999)}/{random.randint(100,999)}",
        })
    return rows

# ──────────────────────────────────────────────
# 2. GSA
# ──────────────────────────────────────────────
def generate_gsa(bescheide):
    rows = []
    counter = 1
    for b in bescheide:
        n_gsa = random.randint(1, 4)
        for g in range(1, n_gsa + 1):
            rows.append({
                "GSA_ID":         f"GSA_DB-{counter:06d}",
                "Bescheid_ID":    b["Bescheid_ID"],
                "GZ":             b["GZ"],
                "Eingabe_GSA":    f"GSA-{g:03d}",
                "GSA_Name":       f"GSA{g:02d}",
                "Anlagenverbund": random.randint(1, 5),
                "Region":         b["Region"],
                "ABM":            b["ABM"],
                "Strecke":        b["Strecke"],
                "Abschnitt":      b["Abschnitt"],
                "km_von":         b["km_von"],
                "km_bis":         b["km_bis"],
                "Ausleitungstyp": random.choice(AUSLEITUNGSTYPEN),
                "§134_erforderlich": b["§134_erforderlich"],
                "Status":         b["Status"],
            })
            counter += 1
    return rows

# ──────────────────────────────────────────────
# 3. INSPEKTIONSELEMENTE
# ──────────────────────────────────────────────
def generate_inspektionselemente(gsa_list):
    rows = []
    counter = 1
    for g in gsa_list:
        if g["Status"] not in ["Produktiv"]:
            continue
        n_el = random.randint(1, 4)
        for _ in range(n_el):
            x = round(random.uniform(480000, 620000), 1)
            y = round(random.uniform(5280000, 5420000), 1)
            rows.append({
                "Element_ID":      f"EL-{counter:06d}",
                "Bescheid_ID":     g["Bescheid_ID"],
                "GZ":              g["GZ"],
                "GSA_ID":          g["Eingabe_GSA"],
                "GSA_Name":        g["GSA_Name"],
                "Elementtyp":      random.choice(ELEMENTTYPEN),
                "X_Koordinate":    x,
                "Y_Koordinate":    y,
                "Bezugssystem":    "ETRS89/UTM",
                "GIS_Status":      "Produktiv",
                "Rueckmeldung_am": fmt(rand_past_date(2)),
                "Bemerkung":       "",
            })
            counter += 1
    return rows

# ──────────────────────────────────────────────
# 4. AUFLAGEN
# ──────────────────────────────────────────────
AUFLAGEN_PROFIL = {
    "Bewilligungsbescheid":    ["B001","B002","B003","W001","W003","W004","W005","G001","L001","L003","GIS001"],
    "Kollaudierungsbescheid":  ["B004","B005","W001","W002","W005","G001","G003","L001","L002","GIS002"],
    "Änderungsbescheid":       ["W001","W003","W004","W005","G001","G002","L003","L004"],
    "Wiederverleihung":        ["W001","W002","W003","W004","W005","W006","G001","G003","G004","L001","L002","L003","L004","L005"],
}

def generate_auflagen(bescheide, gsa_list):
    rows = []
    labor_rows = []
    counter = 1
    lab_counter = 1

    for b in bescheide:
        profil = AUFLAGEN_PROFIL.get(b["Bescheidart"], ["W001","W005","L001"])
        gsa_subset = [g for g in gsa_list if g["Bescheid_ID"] == b["Bescheid_ID"]]

        for auf_id in profil:
            k = KATALOG_MAP.get(auf_id)
            if not k:
                continue
            gsa = random.choice(gsa_subset) if gsa_subset else None
            frist = rand_future_date(1, 5) if k["intervall"] not in ["laufend","BEGL","EINM"] else None

            rows.append({
                "Auflage_DB_ID":          f"AUF-{counter:06d}",
                "Bescheid_ID":            b["Bescheid_ID"],
                "GZ":                     b["GZ"],
                "Auflagen_ID_laut_Bescheid": f"{random.randint(1,50)}. {k['auflagentyp'][:20]}",
                "Auflagentyp":            k["auflagentyp"],
                "Auflagentext":           random.choice(k["beispielsaetze"]),
                "Zielsystem":             k["zielsystem"],
                "GSA_ID":                 gsa["Eingabe_GSA"] if gsa else "",
                "GSA_Name":               gsa["GSA_Name"] if gsa else "",
                "Frist":                  fmt(frist),
                "Intervall":              k["intervall"],
                "Status":                 b["Status"],
                "Rueckmeldung_am":        fmt(rand_past_date(1)) if b["Status"] == "Produktiv" else "",
                "Bemerkung":              "",
            })

            if "parameter" in k and gsa:
                p = k["parameter"]
                messwert = round(p["grenzwert"] * random.uniform(0.3, 1.4), 3)
                labor_rows.append({
                    "Labor_ID":                  f"LAB-{lab_counter:06d}",
                    "Bescheid_ID":               b["Bescheid_ID"],
                    "GZ":                        b["GZ"],
                    "Auflagen_ID_laut_Bescheid":  rows[-1]["Auflagen_ID_laut_Bescheid"],
                    "GSA_ID":                    gsa["Eingabe_GSA"],
                    "GSA_Name":                  gsa["GSA_Name"],
                    "Parameter":                 p["name"],
                    "Grenzwert":                 p["grenzwert"],
                    "Messwert":                  messwert,
                    "Einheit":                   p["einheit"],
                    "Norm":                      p["norm"],
                    "Intervall":                 k["intervall"],
                    "Grenzwert_eingehalten":     "Ja" if messwert <= p["grenzwert"] else "NEIN",
                    "Zielsystem":                k["zielsystem"],
                    "Status":                    b["Status"],
                })
                lab_counter += 1
            counter += 1

    return rows, labor_rows

# ──────────────────────────────────────────────
# 5. DOKUMENTE
# ──────────────────────────────────────────────
def generate_dokumente(bescheide):
    rows = []
    counter = 1
    for b in bescheide:
        n_dok = random.randint(1, 4)
        for _ in range(n_dok):
            hat_link = random.random() > 0.2
            rows.append({
                "Dokument_ID":   f"DOK-{counter:06d}",
                "Bescheid_ID":   b["Bescheid_ID"],
                "GZ":            b["GZ"],
                "Dokumenttyp":   random.choice(DOKUMENTTYPEN),
                "DMS_vorhanden": "Ja" if hat_link else "Nein",
                "DOXIS_Link":    f"https://doxis.aquanet.at/dok/{counter}" if hat_link else "",
                "Status":        b["Status"],
                "Bemerkung":     "",
            })
            counter += 1
    return rows

# ──────────────────────────────────────────────
# CSV EXPORT
# ──────────────────────────────────────────────
def write_csv(rows, name):
    if not rows:
        return
    path = OUT / f"{name}.csv"
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"  OK  {path.name:45s}  ({len(rows)} Zeilen)")

# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────
if __name__ == "__main__":
    print("\n=== Synthetic Company Generator ===")
    print(f"    Unternehmen: {COMPANY['company']['name']}")
    print(f"    Domäne:      {COMPANY['company']['domain']}")
    print()

    bescheide   = generate_bescheide(15)
    gsa         = generate_gsa(bescheide)
    elemente    = generate_inspektionselemente(gsa)
    auflagen, labor = generate_auflagen(bescheide, gsa)
    dokumente   = generate_dokumente(bescheide)

    print("Erzeuge CSV-Dateien:")
    write_csv(bescheide,  "DB_Bescheide")
    write_csv(gsa,        "DB_GSA")
    write_csv(elemente,   "DB_Inspektionselemente")
    write_csv(auflagen,   "DB_Auflagen")
    write_csv(labor,      "DB_LaborGrenzwerte")
    write_csv(dokumente,  "DB_Dokumente")

    print(f"\nZusammenfassung:")
    print(f"  Bescheide:          {len(bescheide)}")
    print(f"  GSA:                {len(gsa)}")
    print(f"  Inspektionselemente:{len(elemente)}")
    print(f"  Auflagen:           {len(auflagen)}")
    print(f"  Laborgrenzwerte:    {len(labor)}")
    print(f"  Dokumente:          {len(dokumente)}")
    print(f"\n  Output: {OUT}")
