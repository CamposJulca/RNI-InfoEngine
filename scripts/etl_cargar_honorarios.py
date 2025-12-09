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


def limpiar_valor(valor):
    """Convierte '$ 3,993,660 ' -> 3993660"""
    if pd.isna(valor):
        return None
    valor = str(valor)
    valor = valor.replace("$", "").replace(",", "").strip()
    return int(valor) if valor.isdigit() else None


def limpiar_cedula(valor):
    """Convierte '1,094,969,260' -> '1094969260'"""
    if pd.isna(valor):
        return None
    valor = str(valor)
    valor = valor.replace(",", "").strip()
    valor = re.sub(r"\.0$", "", valor)
    return valor if valor.isdigit() else None


def cargar_honorarios():
    print("="*70)
    print("        ETL – CARGA DE HONORARIOS MENSUALES")
    print("="*70)

    print("\n[1] Leyendo archivo Excel...")
    df = pd.read_excel(EXCEL_FILE, sheet_name=SHEET_NAME)
    df.columns = [c.strip().upper() for c in df.columns]

    required = {"NUMERO DE CEDULA", "VALOR HONORARIOS MENSUALES ESTIMADOS"}
    if not required.issubset(df.columns):
        print("ERROR: Faltan columnas:", required - set(df.columns))
        return

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    actualizados = 0
    omitidos = 0

    print("\n[2] Procesando filas...\n")

    for i, row in df.iterrows():

        cedula = limpiar_cedula(row["NUMERO DE CEDULA"])
        valor = limpiar_valor(row["VALOR HONORARIOS MENSUALES ESTIMADOS"])

        print("-" * 60)
        print(f"Fila {i+1}")
        print(f" -> Cédula: {cedula}")
        print(f" -> Valor limpio: {valor}")

        if not cedula or valor is None:
            print(" !! Datos inválidos, se omite")
            omitidos += 1
            continue

        # Buscar colaborador
        cur.execute("SELECT id FROM colaborador WHERE cedula = %s", (cedula,))
        col = cur.fetchone()

        if not col:
            print(" !! No existe colaborador en BD → se omite")
            omitidos += 1
            continue

        colaborador_id = col[0]

        # Buscar contrato del colaborador
        cur.execute("""
            SELECT contrato.id
            FROM contrato
            JOIN colaborador_contrato cc ON cc.contrato_id = contrato.id
            WHERE cc.colaborador_id = %s
        """, (colaborador_id,))

        c = cur.fetchone()

        if not c:
            print(" !! No tiene contrato asociado → se omite")
            omitidos += 1
            continue

        contrato_id = c[0]

        # Actualizar contrato.valor
        cur.execute("""
            UPDATE contrato
            SET valor = %s
            WHERE id = %s
        """, (valor, contrato_id))

        print(f" -> Honorario actualizado para contrato {contrato_id}")
        actualizados += 1

    conn.commit()
    cur.close()
    conn.close()

    print("\n========== RESUMEN FINAL ==========")
    print("Honorarios actualizados:", actualizados)
    print("Registros omitidos:", omitidos)
    print("===================================")


if __name__ == "__main__":
    cargar_honorarios()
