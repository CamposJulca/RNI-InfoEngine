import pandas as pd
import psycopg2
import re

# -----------------------------------------
# CONFIG BD
# -----------------------------------------
DB_CONFIG = {
    "dbname": "srni_actividades",
    "user": "postgres",
    "password": "Alejito10.",
    "host": "127.0.0.1",
    "port": 5432
}

FILE = "data/Actividades colaboradores SRNI (2).xlsx"
SHEETS = ["EQUIPO BASE", "PROCEDIMIENTOS"]


# -----------------------------------------
# Helpers
# -----------------------------------------

def limpiar_cedula(valor):
    if pd.isna(valor):
        return None
    v = str(valor).replace(".", "").replace(",", "").strip()
    v = re.sub(r"\.0$", "", v)
    return v if v.isdigit() else None


def normalizar_nombre(nombre):
    if pd.isna(nombre):
        return ""
    return str(nombre).strip()


def buscar_por_nombre(cur, nombre):
    """
    Busca coincidencia exacta ignorando tildes, mayúsculas y espacios repetidos
    """
    cur.execute("""
        SELECT id, cedula, nombre
        FROM colaborador
        WHERE unaccent(upper(nombre)) = unaccent(upper(%s))
    """, (nombre,))
    return cur.fetchone()


def es_cedula_temporal(cedula):
    """
    Identifica cédulas temporales de la forma 10000000X
    """
    if not cedula:
        return False
    return re.match(r"^10000000\d{1,3}$", cedula) is not None


# -----------------------------------------
# ETL PRINCIPAL
# -----------------------------------------

def actualizar_cedulas():
    print("="*80)
    print("            ETL – ACTUALIZACIÓN DE CÉDULAS DE COLABORADORES")
    print("="*80)

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    cambios = 0
    omitidos = 0

    for sheet in SHEETS:
        print(f"\n--- Procesando hoja: {sheet} ---")

        df = pd.read_excel(FILE, sheet_name=sheet)
        df.columns = [c.strip().upper() for c in df.columns]

        if "NO DOCUMENTO IDENTIDAD" not in df.columns or "NOMBRE COLABORADOR" not in df.columns:
            print(f"⚠️  Hoja {sheet} no contiene columnas válidas. Se omite.")
            continue

        for i, row in df.iterrows():
            nombre = normalizar_nombre(row["NOMBRE COLABORADOR"])
            cedula_excel = limpiar_cedula(row["NO DOCUMENTO IDENTIDAD"])

            print(f"\nFila {i+1} -> Nombre: {nombre}, Cédula Excel: {cedula_excel}")

            if not cedula_excel:
                print("   ❌ Cédula inválida → se omite")
                omitidos += 1
                continue

            encontrado = buscar_por_nombre(cur, nombre)
            if not encontrado:
                print("   ❌ No encontrado en BD → se omite")
                omitidos += 1
                continue

            col_id, ced_bd, nom_bd = encontrado

            print(f"   → BD: ID={col_id}, Cédula BD={ced_bd}")

            # Solo actualiza cédulas temporales
            if not es_cedula_temporal(ced_bd):
                print("   ⚠️ Cédula BD NO es temporal → no se actualiza")
                continue

            # Validación: no sobreescribir si la BD ya tiene una real
            if ced_bd == cedula_excel:
                print("   ℹ️ Ya coincide con Excel → nada para hacer")
                continue

            # ACTUALIZAR CÉDULA
            cur.execute("""
                UPDATE colaborador
                SET cedula = %s
                WHERE id = %s
            """, (cedula_excel, col_id))

            print(f"   ✅ Cédula actualizada: {ced_bd} → {cedula_excel}")
            cambios += 1

    conn.commit()
    cur.close()
    conn.close()

    print("\n================ RESUMEN FINAL ================")
    print(f"✔️ Cédulas actualizadas: {cambios}")
    print(f"⛔ Registros omitidos:   {omitidos}")
    print("================================================\n")


if __name__ == "__main__":
    actualizar_cedulas()
