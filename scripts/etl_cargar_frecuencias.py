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

EXCEL_FILE = "data/Actividades colaboradores SRNI (2).xlsx"
SHEETS = ["EQUIPO BASE", "PROCEDIMIENTOS"]


# -------------------------------------------------
# Helpers
# -------------------------------------------------
def limpiar_cedula(valor):
    if pd.isna(valor):
        return None
    v = str(valor).replace(".", "").replace(",", "").strip()
    v = re.sub(r"\.0$", "", v)
    return v if v.isdigit() else None


def split_lines(texto):
    """
    Separa actividades o frecuencias una por línea.
    """
    if not isinstance(texto, str):
        return []
    partes = [p.strip() for p in texto.split("\n") if p.strip()]
    return partes


# -------------------------------------------------
# ETL PRINCIPAL
# -------------------------------------------------
def cargar_actividades_y_frecuencias():
    print("="*80)
    print(" ETL – CARGA DE ACTIVIDADES + FRECUENCIAS SRNI")
    print("="*80)

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    total_insertadas = 0
    omitidos = 0

    for sheet in SHEETS:
        print(f"\n--- Procesando hoja: {sheet} ---")

        df = pd.read_excel(EXCEL_FILE, sheet_name=sheet)
        df.columns = [c.strip().upper() for c in df.columns]

        required = {
            "NO DOCUMENTO IDENTIDAD",
            "ACTIVIDADES QUE DESARROLLA (DESCRIBA UNA A UNA)",
            "FRECUENCIA DE CADA ACTIVIDAD (DIARIA / SEMANAL / MENSUAL / TRIMESTRAL, OTRA ¿CUÁL?)"
        }

        if not required.issubset(df.columns):
            print(f"⚠️  La hoja {sheet} no contiene columnas válidas. Se omite.")
            continue

        for i, row in df.iterrows():
            cedula = limpiar_cedula(row["NO DOCUMENTO IDENTIDAD"])
            actividades_raw = row["ACTIVIDADES QUE DESARROLLA (DESCRIBA UNA A UNA)"]
            frecuencias_raw = row["FRECUENCIA DE CADA ACTIVIDAD (DIARIA / SEMANAL / MENSUAL / TRIMESTRAL, OTRA ¿CUÁL?)"]

            print(f"\nFila {i+1} – Cédula: {cedula}")

            if not cedula:
                print("   ❌ Cédula inválida → omitido")
                omitidos += 1
                continue

            # Buscar colaborador
            cur.execute("SELECT id, nombre FROM colaborador WHERE cedula=%s", (cedula,))
            col = cur.fetchone()

            if not col:
                print("   ❌ No existe colaborador con esa cédula → omitido")
                omitidos += 1
                continue

            col_id, col_nombre = col
            print(f"   → Colaborador encontrado: {col_nombre} (id={col_id})")

            actividades = split_lines(actividades_raw)
            frecuencias = split_lines(frecuencias_raw)

            print(f"   Actividades detectadas: {len(actividades)}")
            print(f"   Frecuencias detectadas: {len(frecuencias)}")

            # Alinear frecuencias
            if len(frecuencias) < len(actividades):
                frecuencias += ["Sin frecuencia"] * (len(actividades) - len(frecuencias))

            # Eliminar actividades previas del colaborador
            cur.execute("DELETE FROM actividad WHERE colaborador_id=%s", (col_id,))

            # Insertar nuevas
            for act, freq in zip(actividades, frecuencias):
                cur.execute("""
                    INSERT INTO actividad (colaborador_id, descripcion, frecuencia)
                    VALUES (%s, %s, %s)
                """, (col_id, act, freq))

                print(f"   ✔ Insertada: '{act}' – Frecuencia: {freq}")
                total_insertadas += 1

    conn.commit()
    cur.close()
    conn.close()

    print("\n================== RESUMEN FINAL ==================")
    print(f"✔ Actividades insertadas: {total_insertadas}")
    print(f"⛔ Registros omitidos:   {omitidos}")
    print("===================================================")


if __name__ == "__main__":
    cargar_actividades_y_frecuencias()
