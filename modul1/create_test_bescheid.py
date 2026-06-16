"""
Erstellt einen synthetischen Wasserrechts-Bescheid als PDF zum Testen von Modul 1.
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from pathlib import Path

OUT = Path(__file__).parent / "output"
OUT.mkdir(exist_ok=True)

def create_bescheid():
    pdf_path = OUT / "test_bescheid_WA1-W-47832-021.pdf"
    doc = SimpleDocTemplate(str(pdf_path), pagesize=A4,
                            topMargin=2.5*cm, bottomMargin=2.5*cm,
                            leftMargin=2.5*cm, rightMargin=2.5*cm)

    styles = getSampleStyleSheet()
    normal = styles["Normal"]
    normal.fontName = "Helvetica"
    normal.fontSize = 10
    normal.leading = 14

    h1 = ParagraphStyle("h1", parent=normal, fontSize=13, fontName="Helvetica-Bold",
                        spaceAfter=6, spaceBefore=12)
    h2 = ParagraphStyle("h2", parent=normal, fontSize=11, fontName="Helvetica-Bold",
                        spaceAfter=4, spaceBefore=10)
    center = ParagraphStyle("center", parent=normal, alignment=1)
    bold = ParagraphStyle("bold", parent=normal, fontName="Helvetica-Bold")

    story = []

    # Kopf
    story.append(Paragraph("BEZIRKSHAUPTMANNSCHAFT KORNEUBURG", center))
    story.append(Paragraph("Abteilung Wasserrecht", center))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("BESCHEID", ParagraphStyle("title", parent=center,
                            fontSize=16, fontName="Helvetica-Bold")))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("GZ: WA1-W-47832/021", bold))
    story.append(Paragraph("Datum: 14. März 2022", normal))
    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph("Antragstellerin:", bold))
    story.append(Paragraph("AquaNet Infrastruktur GmbH, Hauptstraße 1, 1010 Wien", normal))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph(
        "Die Bezirkshauptmannschaft Korneuburg erteilt der AquaNet Infrastruktur GmbH "
        "gemäß §§ 10, 12 und 111 WRG 1959 die wasserrechtliche <b>Bewilligung</b> für die "
        "Errichtung und den Betrieb einer Wasserversorgungsanlage im Bereich der Strecke "
        "Donaukorridor, km 12,4 bis km 18,7, Abschnitt A03, Region Ost.", normal))
    story.append(Spacer(1, 0.5*cm))

    # Auflagen
    story.append(Paragraph("AUFLAGEN UND BEDINGUNGEN", h1))
    story.append(Paragraph(
        "Die Bewilligung wird unter folgenden Auflagen und Bedingungen erteilt:", normal))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("I. Bauphase", h2))

    auflagen_bau = [
        ("1.", "Ölbindemittel bereitstellen",
         "Auf der Baustelle sind stets ausreichende Mengen an Ölbindemitteln bereitzuhalten. "
         "Die Menge muss mindestens 50 kg betragen und ist in einem verschlossenen, "
         "beschrifteten Behälter am Baustelleneingang zu lagern."),
        ("2.", "Baustellensicherung",
         "Die Baustelle ist gemäß § 90 StVO ordnungsgemäß abzusichern und zu beleuchten. "
         "Während der gesamten Bauphase ist eine Verkehrssicherung sicherzustellen."),
        ("3.", "Erdarbeiten Protokoll",
         "Über sämtliche Erdarbeiten im Gewässerbereich ist ein lückenloses Bautagebuch "
         "zu führen. Das Bautagebuch ist der Behörde auf Verlangen vorzulegen."),
        ("4.", "Uferböschung wiederherstellen",
         "Nach Abschluss der Bauarbeiten sind alle Uferböschungen und Dammkronen "
         "fachgerecht wiederherzustellen und mit standortgerechten Gehölzen zu bepflanzen."),
        ("5.", "Schutzstreifen Vegetation",
         "Entlang der Gewässerufer ist ein Schutzstreifen von mindestens 5 Metern Breite "
         "von Bebauung freizuhalten. In diesem Bereich sind ausschließlich standortgerechte "
         "Gehölze zu pflanzen."),
    ]

    for nr, titel, text in auflagen_bau:
        story.append(Paragraph(f"<b>{nr} {titel}:</b>", normal))
        story.append(Paragraph(text, normal))
        story.append(Spacer(1, 0.2*cm))

    story.append(Paragraph("II. Betrieb", h2))

    auflagen_betrieb = [
        ("6.", "Wassermengenmonitoring",
         "Die entnommene Wassermenge ist kontinuierlich zu messen und monatlich im "
         "Elektronischen Betriebsbuch (EBeH) zu dokumentieren. Die maximale Entnahmemenge "
         "beträgt 1.200 m3/Tag."),
        ("7.", "Wasserqualitätsprüfung pH-Wert",
         "Der pH-Wert des eingeleiteten Wassers ist wöchentlich zu messen. "
         "Der Grenzwert beträgt 6,5 - 8,5 pH. Die Messergebnisse sind im "
         "Probenahmeübersichtsplan zu dokumentieren."),
        ("8.", "Sauerstoffgehalt Messung",
         "Der Sauerstoffgehalt im Ablauf ist monatlich zu messen und zu protokollieren. "
         "Der Mindestwert beträgt 6,0 mg/l O2. Bei Unterschreitung ist unverzüglich "
         "die Behörde zu informieren."),
        ("9.", "Trübung Kontrolle",
         "Die Trübung des Abwassers ist nach Regenereignissen zu kontrollieren und zu "
         "protokollieren. Grenzwert: 10 NTU. Ergebnisse sind im EBeH einzutragen."),
        ("10.", "Jährliche Inspektion Bauwerke",
         "Alle Einlauf- und Auslaufbauwerke sind jährlich auf Schäden und Funktionsfähigkeit "
         "zu inspizieren. Das Inspektionsprotokoll ist im EBeH zu hinterlegen."),
        ("11.", "GIS-Einmessung",
         "Sämtliche neu errichteten Bauwerke (Einlaufbauwerke, Auslaufbauwerke, Schieber) "
         "sind nach Fertigstellung im Koordinatensystem ETRS89/UTM einzumessen und im "
         "GIS-System ArcGIS zu erfassen."),
    ]

    for nr, titel, text in auflagen_betrieb:
        story.append(Paragraph(f"<b>{nr} {titel}:</b>", normal))
        story.append(Paragraph(text, normal))
        story.append(Spacer(1, 0.2*cm))

    story.append(Paragraph("III. Grünflächen und Ökologie", h2))

    auflagen_oek = [
        ("12.", "Ökologische Begleitmaßnahmen",
         "Während der Bauphase ist eine ökologische Baubegleitung durch einen "
         "qualifizierten Ökologen sicherzustellen. Die Begleitprotokolle sind "
         "vierteljährlich im GUSTAV-System zu dokumentieren."),
        ("13.", "Amphibienschutz",
         "Im Bereich der Laichgewässer (Strecke km 14,2 - km 15,8) sind zwischen "
         "1. März und 31. Mai keine Erdarbeiten durchzuführen (Amphibierschutzzeit). "
         "Ausnahmen bedürfen der behördlichen Genehmigung."),
    ]

    for nr, titel, text in auflagen_oek:
        story.append(Paragraph(f"<b>{nr} {titel}:</b>", normal))
        story.append(Paragraph(text, normal))
        story.append(Spacer(1, 0.2*cm))

    # Befristung
    story.append(Paragraph("BEFRISTUNG", h1))
    story.append(Paragraph(
        "Die wasserrechtliche Bewilligung wird bis zum <b>31. Dezember 2042</b> befristet. "
        "Ein Antrag auf Wiederverleihung ist spätestens 12 Monate vor Ablauf der "
        "Befristung bei der zuständigen Wasserrechtsbehörde einzubringen.", normal))
    story.append(Spacer(1, 0.5*cm))

    # Rechtsmittelbelehrung
    story.append(Paragraph("RECHTSMITTELBELEHRUNG", h2))
    story.append(Paragraph(
        "Gegen diesen Bescheid kann innerhalb von vier Wochen ab Zustellung Beschwerde "
        "an das Landesverwaltungsgericht Niederösterreich erhoben werden.", normal))
    story.append(Spacer(1, 1*cm))

    story.append(Paragraph("Für die Bezirkshauptmannschaft Korneuburg:", normal))
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph("Mag. Christine Huber", normal))
    story.append(Paragraph("Leiterin Wasserrechtsabteilung", normal))

    doc.build(story)
    print(f"PDF erstellt: {pdf_path}")
    return str(pdf_path)

if __name__ == "__main__":
    path = create_bescheid()
    print(f"\nJetzt verarbeiten mit:")
    print(f"  cd C:\\Users\\samba\\Desktop\\ClaudeEWMS\\modul1")
    print(f"  py bescheid_processor.py \"{path}\"")
