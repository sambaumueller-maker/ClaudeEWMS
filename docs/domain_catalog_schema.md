# Domänenübergreifendes Katalogschema
# KI-Fachsystem-Generator — Fundament

Version: 0.1 | Status: Entwurf | Datum: 2026-06-16

---

## 1. Grundprinzip

Jedes Fachsystem das wir generieren basiert auf demselben abstrakten Schema.
Die Domäne (Wasserrecht, UVP, Baurecht...) füllt dieses Schema mit Inhalten.
Das Schema selbst ändert sich nie.

```
BESCHEID / GENEHMIGUNG
  └── FACHBEREICH (Schutzgut / Rechtsgebiet)
       └── AUFLAGENTYP (katalogisiert)
            ├── MASSNAHMENTYP
            ├── PHASE
            ├── PFLICHTPARAMETER
            ├── ZIELSYSTEM
            └── AUFGABE → DASHBOARD
```

---

## 2. Abstraktes Katalogschema (domain-agnostic)

### 2.1 Haupttabelle: AUFLAGEN_KATALOG

| Feld | Typ | Beschreibung | Beispiel Wasserrecht | Beispiel UVP |
|---|---|---|---|---|
| Auflagen_ID | String | Eindeutige ID | W001 | L001 |
| Domäne | Enum | Rechtsgebiet | Wasserrecht | UVP-G |
| Fachbereich | String | Schutzgut / Kategorie | Betrieb Wasser | Lärm |
| Auflagentyp | String | Standardbezeichnung | Mahd durchführen | Lärmschutzwand errichten |
| Synonyme | Array[String] | Alternative Formulierungen | ["Mähen", "Böschungsmahd"] | ["Lärmschutz errichten"] |
| Beispielsätze | Array[String] | Reale Bescheidformulierungen (für KI-Training) | ["Die Böschungen sind..."] | ["Zum Schutz der Anrainer..."] |
| Maßnahmentyp | Enum | Vermeidung / Verminderung / Ausgleich / Monitoring | Betrieb | Vermeidung |
| Phase | Enum | Bau / Betrieb / Nachsorge / Einmalig | Betrieb | Bauphase |
| Pflichtparameter | Array[String] | Felder die bei Erfassung ausgefüllt werden müssen | ["Fläche_m2", "Häufigkeit"] | ["Länge_m", "Höhe_m"] |
| Zielsystem | String | Zielplattform für Aufgabe | EBeH | Lärmmonitoring-System |
| Dashboard_Kategorie | String | KPI-Gruppe im Dashboard | Grünpflege | Immissionsschutz |
| Intervall | Enum | einmalig / jährlich / halbjährlich / monatlich / laufend | 2x jährlich | einmalig |
| Standardverantwortlicher | String | Fachbereich / Rolle | Betrieb | Ökologische Bauaufsicht |
| Gesetzliche_Grundlage | String | Rechtsgrundlage | WRG §32 | UVP-G Anhang 1 |
| KI_Konfidenz_Schwelle | Float | Minimum für Auto-Vorschlag (0.0–1.0) | 0.80 | 0.75 |
| Aktiv | Boolean | Im System verwendbar | true | true |
| Gültig_ab | Date | Versionierung | 2024-01-01 | 2024-01-01 |
| Gültig_bis | Date | Versionierung | null | null |
| Version | Integer | Änderungshistorie | 1 | 1 |

### 2.2 Nebentabelle: AUFLAGEN_PARAMETER

Für Auflagentypen die messbare Werte benötigen (Labor, Lärm, Luft):

| Feld | Typ | Beschreibung |
|---|---|---|
| Parameter_ID | String | Eindeutige ID |
| Auflagen_ID | String | FK → AUFLAGEN_KATALOG |
| Parameter | String | Name des Messparameters |
| Grenzwert | Decimal | Referenzwert |
| Einheit | String | mg/l, dB, µg/m³, ... |
| Grenzwerttyp | Enum | Maximum / Minimum / Zielwert |
| Norm / Rechtsgrundlage | String | z.B. EU-VO 2023/915, IG-L |
| Intervall | Enum | Messintervall |
| Messmethode | String | z.B. DIN EN ISO 11885 |

### 2.3 Nebentabelle: AUFLAGEN_SYNONYME (erweiterbar durch KI)

| Feld | Typ | Beschreibung |
|---|---|---|
| Synonym_ID | String | Eindeutige ID |
| Auflagen_ID | String | FK → AUFLAGEN_KATALOG |
| Synonym_Text | String | Alternative Formulierung |
| Quelle | Enum | Manuell / KI-Vorschlag / Bescheid-Import |
| Konfidenz | Float | Bei KI-Herkunft |
| Freigegeben | Boolean | Durch Fachprüfer freigegeben |

---

## 3. Domänen und Fachbereiche

### 3.1 Domäne: Wasserrecht (WRG)

| Fachbereich_ID | Fachbereich | Kürzel | Primäres Zielsystem |
|---|---|---|---|
| WRG-BAU | Bau (Gewässerschutz) | B | EBauH |
| WRG-BET | Betrieb Wasser | W | EBeH |
| WRG-GRN | Grünflächen | G | GUSTAV |
| WRG-LAB | Laborprogramm | L | Probenahmeübersichtsplan |
| WRG-GIS | Inspektionselemente / GIS | GIS | GIS |

### 3.2 Domäne: UVP / Infrastruktur (UVP-G)

| Fachbereich_ID | Fachbereich | Kürzel | Primäres Zielsystem |
|---|---|---|---|
| UVP-LAE | Lärm | LAE | Lärmmonitoring |
| UVP-LUF | Luftschadstoffe | LUF | Luftmessnetz |
| UVP-ERB | Erschütterungen | ERB | Erschütterungsmonitoring |
| UVP-LIC | Licht & Beschattung | LIC | Lichtmonitoring |
| UVP-GRW | Grundwasser | GRW | GW-Monitoring |
| UVP-BOD | Boden | BOD | Bodenmonitoring |
| UVP-FAU | Fauna | FAU | ÖBA-System / GIS |
| UVP-FLO | Flora / Vegetation | FLO | ÖBA-System / GIS |
| UVP-FOR | Forst / Rodung | FOR | Forstverwaltung |
| UVP-NAT | Naturschutz | NAT | GIS |
| UVP-SOZ | Siedlungsraum / Soziales | SOZ | Projektmanagement |

### 3.3 Domäne: Baurecht (BO) — geplant

| Fachbereich_ID | Fachbereich |
|---|---|
| BO-STA | Statik / Standsicherheit |
| BO-BRA | Brandschutz |
| BO-ENE | Energieausweis |
| BO-BAR | Barrierefreiheit |

---

## 4. Maßnahmentypen

Universell gültig für alle Domänen:

| Typ | Code | Beschreibung | Wann |
|---|---|---|---|
| Vermeidungsmaßnahme | VERM | verhindert Einwirkung von Anfang an | Planung / Bau |
| Verminderungsmaßnahme | VERM2 | reduziert unvermeidliche Einwirkung | Bau / Betrieb |
| Ausgleichsmaßnahme | AUSG | kompensiert verbleibende Einwirkung | Betrieb / Nachsorge |
| Beweissicherung | BEWS | Zustandsdokumentation vor Beginn | Vor Bau |
| Begleitende Kontrolle | BEGL | laufende Überprüfung | Bau / Betrieb |
| Monitoring | MONI | systematische Langzeitüberwachung | Betrieb / Nachsorge |
| Einmalige Maßnahme | EINM | nur einmal erforderlich | Bau oder Betriebsbeginn |
| Periodische Maßnahme | PERI | wiederkehrend nach Intervall | Betrieb |

---

## 5. Phasen

| Phase | Code | Beschreibung |
|---|---|---|
| Planungsphase | PLAN | vor Baubeginn |
| Bauphase | BAU | während Bauarbeiten |
| Betriebsphase | BET | laufender Betrieb |
| Nachsorgephase | NACH | nach Stilllegung |
| Einmalig | EINM | phasenneutral, einmal |

---

## 6. KI-Klassifikationslogik

### 6.1 Input → Output

```
INPUT:  Freitext aus Bescheid
        "Die Böschungen sind mindestens zweimal jährlich zu mähen
         und das Mähgut ist abzutragen."

SCHRITT 1: Tokenisierung & Normalisierung
SCHRITT 2: Matching gegen Synonyme + Beispielsätze
SCHRITT 3: Konfidenz-Score berechnen
SCHRITT 4: Vorschlag mit Begründung

OUTPUT:
  Auflagen_ID:         W001
  Auflagentyp:         Mahd durchführen
  Fachbereich:         Grünflächen
  Zielsystem:          GUSTAV
  Intervall:           2x jährlich
  Konfidenz:           0.94
  Begründung:          "Treffer 'mähen' in Synonymen, 'zweimal jährlich' → Intervall"
  Alternativvorschlag: W002 (Mulchen, Konfidenz 0.61)
```

### 6.2 Konfidenz-Schwellen

| Konfidenz | Aktion |
|---|---|
| ≥ 0.90 | Vorschlag mit grüner Markierung — Prüfer bestätigt nur |
| 0.70–0.89 | Vorschlag mit gelber Markierung — Prüfer prüft aktiv |
| < 0.70 | Kein Vorschlag — manuelle Zuordnung erforderlich |
| Kein Treffer | Neuer Auflagentyp → Vorschlag für Katalogerweiterung |

---

## 7. Erweiterungslogik — Continuous Improvement

Wenn die KI einen Text nicht zuordnen kann:

```
NICHT ZUGEORDNET: "Der Parameter Selen ist halbjährlich zu messen."

→ Vorschlag: Neuer Laborparameter "Selen"
→ Vorschlag: Neuer Auflagentyp L007 "Selen messen"
→ Status: VORSCHLAG — wartet auf Fachprüfer-Freigabe
→ Nach Freigabe: automatisch in AUFLAGEN_KATALOG übernommen
```

Gespeichert wird NUR:
- Auflagentyp (abstrakt)
- Parameter (abstrakt)
- Synonyme (abstrakt)

NICHT gespeichert:
- Kundenname
- Bescheidinhalt
- Projektdaten

---

## 8. Synthetic Company Generator — Anforderungen

Der Generator muss für jede synthetische Firma erzeugen:

### 8.1 Unternehmensstruktur
- Name, Branche, Domäne(n)
- Organigramm mit Rollen
- Zielsysteme (kundenspezifisch)

### 8.2 Bescheide (synthetisch)
- Pro Domäne: 3–10 Bescheide
- Realistisches Datum, Behörde, GZ
- Korrekte Auflagenanzahl pro Bescheidtyp

### 8.3 Auflagen (aus Katalog)
- Zufällige aber plausible Auswahl aus Katalog
- Korrekte Zuordnung zu Zielsystemen
- Realistische Grenzwerte (Labor)
- Plausible Fristen und Intervalle

### 8.4 Statusverteilung (realistisch)
- 60% Produktiv / Freigegeben
- 20% In Bearbeitung
- 10% Prüfung offen
- 10% Neu / Entwurf

### 8.5 Zeitreihen (für Dashboard)
- Historische Prüfdaten (3 Jahre)
- Messwerte mit Trend (Labor)
- Fristkalender

---

## 9. Offene Fragen (Wissenslücken)

| Nr | Frage | Priorität |
|---|---|---|
| 1 | Welche konkreten Zielsysteme hat ein typischer UVP-Auftraggeber? | Hoch |
| 2 | Wie heißen Lärmmonitoring-Systeme in der Praxis? | Mittel |
| 3 | Gibt es Normgrenzwerte für Erschütterungen die wir verwenden können? | Mittel |
| 4 | Welche Rolle hat die "Ökologische Bauaufsicht" — ist das intern oder extern? | Hoch |
| 5 | Wie lange ist die typische Nachsorgephase nach UVP-Projekten? | Niedrig |
| 6 | Gibt es öffentlich zugängliche Bescheid-Datenbanken in Österreich? (EDOK, RIS) | Hoch |
