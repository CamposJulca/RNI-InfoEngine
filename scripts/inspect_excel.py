import pandas as pd

FILE = "data/Actividades colaboradores SRNI (1).xlsx"
SHEET = "EQUIPO BASE"

df = pd.read_excel(FILE, sheet_name=SHEET)

print("\nCOLUMNAS EXACTAS ENCONTRADAS:")
for c in df.columns:
    print(f"- {c}  ||  NORMALIZADA -> {c.strip().upper()}")
