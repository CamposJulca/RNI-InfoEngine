import pandas as pd
import psycopg2
import re

DB_CONFIG = {
    "dbname": "srni_actividades",
    "user": "postgres",
    "password": "Alejito10.",
    "host": "127.0.0.1",
    "port": 5432
}

EXCEL_FILE = "data/Copia de 15092025 MATRIZ NECESIDADES 2026 SRNI.xlsx"
SHEET_NAME = "Prestación de Servicios"

# ------------------------------
# Normalizar campos
# ------------------------------

def limpiar_cedula(valor):
    if pd.isna(valor):
        return None
    valor = str(valor).replace(",", "").strip()
    valor = re.sub(r"\.0$", "", valor)
    return valor if valor.isdigit() else None


def normalizar_vinculacion(valor):
    if pd.isna(valor):
        return None

    v = str(valor).strip().upper()
    v = v.replace("\n", " ").replace("  ", " ")

    if "CPS" in v:
        return "CPS"
    if "OPERADOR" in v:
        return "OPERADOR"

    return "OTRO"


# ------------------------------
# PROCESO PRINCIPAL
# ------------------------------

def cargar_vinculacion():
    print("="*70)
    print("     ETL – ACTUALIZACIÓN DE VINCULACIÓN ACTUAL (CPS/OPERADOR)")
    print("="*70)

    print("[1] Cargando Excel...")
    df = pd.read_excel(EXCEL_FILE, sheet_name=SHEET_NAME)
    df.columns = [c.strip().upper() for c in df.columns]

    required = {"NUMERO DE CEDULA", "VINCULACION ACTUAL\n(CPS-OPERADOR)"}
    if not required.issubset(df.columns):
        print("ERROR: Faltan columnas:", required - set(df.columns))
        return

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    actualizados = 0
    omitidos = 0

    print("\n[2] Procesando filas...")
    print("-"*60)

    for i, row in df.iterrows():
        cedula = limpiar_cedula(row["NUMERO DE CEDULA"])
        vinculacion_raw = row["VINCULACION ACTUAL\n(CPS-OPERADOR)"]

        print(f"\nFila {i+1}")
        print(f" -> Cédula limpia: {cedula}")

        if not cedula:
            print(" !! Cédula inválida → se omite")
            omitidos += 1
            continue

        vinculacion = normalizar_vinculacion(vinculacion_raw)
        print(f" -> Vinculación normalizada: {vinculacion}")

        cur.execute("SELECT id FROM colaborador WHERE cedula = %s", (cedula,))
        res = cur.fetchone()

        if not res:
            print(" !! No existe colaborador con esta cédula → se omite")
            omitidos += 1
            continue

        colaborador_id = res[0]

        cur.execute("""
            UPDATE colaborador
            SET vinculacion_actual = %s
            WHERE id = %s
        """, (vinculacion, colaborador_id))

        print(" -> Vinculación actualizada")
        actualizados += 1

    conn.commit()
    cur.close()
    conn.close()

    print("\n=========== RESUMEN FINAL ===========")
    print("Registros actualizados:", actualizados)
    print("Omitidos:", omitidos)
    print("=======================================")


if __name__ == "__main__":
    cargar_vinculacion()
