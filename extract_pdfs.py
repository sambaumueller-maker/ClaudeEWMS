import pdfplumber

files = [
    ('Antrag', r'C:\Users\samba\AppData\Local\Temp\SA_A-01_C_Ber_Antrag.pdf', [0,1,2,3,4]),
    ('Zusammenfassung', r'C:\Users\samba\AppData\Local\Temp\SA_B-01-01_D_Ber_Zusammenfassung (1).pdf', [0,1,2,3]),
    ('UVE_Synthese', r'C:\Users\samba\AppData\Local\Temp\Vergleichsdokument_SA_D-02_Ber_C_D_UVESynthesebericht (1).pdf', [0,1,2,3,4,5]),
    ('Massnahmen', r'C:\Users\samba\AppData\Local\Temp\Vergleichsdokument_SA_B-06-01-1001_TB_C_D_Maßnahmen (1).pdf', [0,1,2,3,4,5,6,7]),
    ('Entwässerung', r'C:\Users\samba\AppData\Local\Temp\B-02-08-1001_Bericht_Entwässerung_Vergleich_B-C (1).pdf', [0,1,2,3]),
    ('Bauphasen', r'C:\Users\samba\AppData\Local\Temp\B-05-01-1001_Berichtevergleich_Bauphasen_Verbesserung-2014_2016 (1).pdf', [0,1,2,3]),
    ('Rodung', r'C:\Users\samba\AppData\Local\Temp\B-07-01-1001_Bericht_Rodung_Vergleich_B-C (1).pdf', [0,1,2]),
]

for name, path, pages in files:
    print("\n" + "="*60)
    print("### " + name)
    print("="*60)
    try:
        with pdfplumber.open(path) as pdf:
            for i in pages:
                if i < len(pdf.pages):
                    text = pdf.pages[i].extract_text()
                    if text:
                        print("-- Seite " + str(i+1) + " --")
                        print(text[:2500])
    except Exception as e:
        print("Fehler: " + str(e))
