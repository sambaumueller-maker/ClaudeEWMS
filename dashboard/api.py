"""
AquaNet Dashboard API — FastAPI Backend
"""
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from pathlib import Path
import csv, json, os, sys, tempfile

app = FastAPI(title="AquaNet Dashboard")

BASE = Path(__file__).parent
DATA = BASE.parent / "synthetic_generator" / "output"
COMPANY_DEF = BASE.parent / "synthetic_generator" / "company_definition.json"
KATALOG_FILE = BASE.parent / "synthetic_generator" / "auflagen_katalog.json"
CONFIG_FILE = BASE / "config.json"
MODUL1_OUT = BASE.parent / "modul1" / "output"
MODUL1_OUT.mkdir(parents=True, exist_ok=True)

def read_csv(name):
    path = DATA / f"{name}.csv"
    if not path.exists():
        return []
    with open(path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def read_config():
    if not CONFIG_FILE.exists():
        return {"anthropic_api_key": ""}
    with open(CONFIG_FILE, encoding="utf-8") as f:
        return json.load(f)

def write_config(data):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

@app.get("/")
def index():
    return FileResponse(BASE / "static" / "index.html")

@app.get("/api/company")
def company():
    with open(COMPANY_DEF, encoding="utf-8") as f:
        return json.load(f)

@app.get("/api/katalog")
def katalog():
    with open(KATALOG_FILE, encoding="utf-8") as f:
        return json.load(f)

@app.get("/api/bescheide")
def bescheide():
    return read_csv("DB_Bescheide")

@app.get("/api/gsa")
def gsa():
    return read_csv("DB_GSA")

@app.get("/api/auflagen")
def auflagen():
    return read_csv("DB_Auflagen")

@app.get("/api/labor")
def labor():
    return read_csv("DB_LaborGrenzwerte")

@app.get("/api/dokumente")
def dokumente():
    return read_csv("DB_Dokumente")

@app.get("/api/inspektionselemente")
def inspektionselemente():
    return read_csv("DB_Inspektionselemente")

@app.get("/api/kpis")
def kpis():
    bescheide_list = read_csv("DB_Bescheide")
    auflagen_list  = read_csv("DB_Auflagen")
    labor_list     = read_csv("DB_LaborGrenzwerte")
    gsa_list       = read_csv("DB_GSA")
    dok_list       = read_csv("DB_Dokumente")

    def count_status(rows, field, val):
        return sum(1 for r in rows if r.get(field) == val)

    labor_ok  = sum(1 for r in labor_list if r.get("Grenzwert_eingehalten") == "Ja")
    labor_nok = sum(1 for r in labor_list if r.get("Grenzwert_eingehalten") == "NEIN")

    zielsystem_counts = {}
    for a in auflagen_list:
        zs = a.get("Zielsystem", "Unbekannt")
        zielsystem_counts[zs] = zielsystem_counts.get(zs, 0) + 1

    status_counts = {}
    for b in bescheide_list:
        s = b.get("Status", "Unbekannt")
        status_counts[s] = status_counts.get(s, 0) + 1

    return {
        "bescheide_gesamt":    len(bescheide_list),
        "bescheide_produktiv": count_status(bescheide_list, "Status", "Produktiv"),
        "bescheide_offen":     count_status(bescheide_list, "Status", "Prüfung offen"),
        "gsa_gesamt":          len(gsa_list),
        "auflagen_gesamt":     len(auflagen_list),
        "auflagen_offen":      count_status(auflagen_list, "Status", "Prüfung offen"),
        "labor_gesamt":        len(labor_list),
        "labor_ok":            labor_ok,
        "labor_nok":           labor_nok,
        "dokumente_gesamt":    len(dok_list),
        "zielsystem_counts":   zielsystem_counts,
        "status_counts":       status_counts,
    }

# ── Modul 1 ──────────────────────────────────────────────

@app.get("/api/settings")
def get_settings():
    cfg = read_config()
    key = cfg.get("anthropic_api_key", "")
    return {"api_key_set": bool(key), "api_key_preview": f"{key[:8]}..." if key else ""}

class SettingsBody(BaseModel):
    anthropic_api_key: str

@app.post("/api/settings")
def save_settings(body: SettingsBody):
    cfg = read_config()
    cfg["anthropic_api_key"] = body.anthropic_api_key.strip()
    write_config(cfg)
    return {"ok": True, "message": "API-Key gespeichert"}

@app.post("/api/modul1/process")
async def modul1_process(file: UploadFile = File(...)):
    cfg = read_config()
    api_key = cfg.get("anthropic_api_key", "").strip()
    if not api_key:
        raise HTTPException(status_code=400, detail="Kein Anthropic API-Key gesetzt. Bitte zuerst in den Einstellungen speichern.")

    # PDF temporär speichern
    suffix = Path(file.filename).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        sys.path.insert(0, str(BASE.parent / "modul1"))
        os.environ["ANTHROPIC_API_KEY"] = api_key
        import bescheid_processor as bp
        import importlib
        importlib.reload(bp)

        katalog = bp.load_katalog()
        pdf_text = bp.extract_pdf_text(tmp_path)
        result = bp.classify_with_claude(pdf_text, katalog)

        # Ergebnis speichern
        stem = Path(file.filename).stem
        out_file = MODUL1_OUT / f"{stem}_analyse.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        return result
    finally:
        os.unlink(tmp_path)

@app.get("/api/modul1/analysen")
def modul1_analysen():
    if not MODUL1_OUT.exists():
        return []
    results = []
    for f in sorted(MODUL1_OUT.glob("*_analyse.json")):
        with open(f, encoding="utf-8") as fh:
            data = json.load(fh)
        data["_dateiname"] = f.name
        results.append(data)
    return results

app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
