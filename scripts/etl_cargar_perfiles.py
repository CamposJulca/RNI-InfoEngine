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
SHEET_NAME = "Prestación de Servicios"   # <-- HOJA CORRECTA


def limpiar_cedula(valor):
    """Limpia comas, espacios y .0, y valida que quede solo dígitos."""
    if pd.isna(valor):
        return None
    valor = str(valor).strip()
    valor = valor.replace(",", "")
    valor = re.sub(r"\.0$", "", valor)
    return valor if valor.isdigit() else None


def cargar_perfiles():
    print("="*70)
    print("      ETL – ACTUALIZACIÓN DE PERFILES DE COLABORADORES")
    print("="*70)

    print("\n[1] Leyendo archivo Excel (hoja 'Prestación de Servicios')...")
    df = pd.read_excel(EXCEL_FILE, sheet_name=SHEET_NAME)

    print("\n[2] Columnas crudas encontradas en el Excel:")
    print(df.columns.tolist())

    print("\n[3] Información del DataFrame:")
    print(df.info())

    print("\n[4] Primeras filas del DataFrame:")
    print(df.head())

    # Normalizar columnas
    df.columns = [c.strip().upper() for c in df.columns]

    print("\n[5] Columnas normalizadas:")
    print(df.columns.tolist())

    required = {"NUMERO DE CEDULA", "PERFIL"}

    print("\n[6] Validando columnas requeridas...")
    if not required.issubset(df.columns):
        print("ERROR: Faltan columnas:", required - set(df.columns))
        print("\n**DETALLE:** La hoja correcta sí existe, pero revisa si las columnas están bien escritas.")
        return

    print(" -> Columnas válidas.")

    # Conexión a BD
    print("\n[7] Conectando a PostgreSQL...")
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    actualizados = 0
    omitidos = 0

    print("\n[8] Procesando filas...\n")

    for i, row in df.iterrows():
        print("-" * 60)
        cedula = limpiar_cedula(row["NUMERO DE CEDULA"])
        perfil = str(row["PERFIL"]).strip()

        print(f"Fila {i+1}")
        print(f" -> Cédula limpia: {cedula}")
        print(f" -> Perfil: {perfil[:50]}...")

        if not cedula:
            print(" !! Cédula inválida → Se omite")
            omitidos += 1
            continue

        cur.execute("SELECT id FROM colaborador WHERE cedula = %s", (cedula,))
        result = cur.fetchone()

        if not result:
            print(" !! No existe colaborador con esa cédula → Se omite")
            omitidos += 1
            continue

        colaborador_id = result[0]

        cur.execute("""
            UPDATE colaborador
            SET perfil = %s
            WHERE id = %s
        """, (perfil, colaborador_id))

        print(" -> Perfil actualizado correctamente")
        actualizados += 1

    conn.commit()
    cur.close()
    conn.close()

    print("\n================= RESUMEN FINAL =================")
    print(f"Perfiles actualizados: {actualizados}")
    print(f"Registros omitidos:    {omitidos}")
    print("=================================================")


if __name__ == "__main__":
    cargar_perfiles()
