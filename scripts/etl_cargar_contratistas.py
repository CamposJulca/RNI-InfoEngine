import pandas as pd
import psycopg2

DB_CONFIG = {
    "dbname": "srni_actividades",
    "user": "postgres",
    "password": "Alejito10.",
    "host": "127.0.0.1",
    "port": 5432
}

EXCEL_FILE = "data/02102025 Listado contratos SRNI.xlsx"
SHEET_NAME = 0


# -----------------------------------------------------------
# Helpers
# -----------------------------------------------------------
def obtener_o_crear_equipo(cur, nombre_equipo):
    nombre_equipo = nombre_equipo.strip()
    cur.execute("SELECT id FROM equipo WHERE nombre=%s", (nombre_equipo,))
    row = cur.fetchone()
    if row:
        return row[0]

    cur.execute(
        "INSERT INTO equipo (nombre) VALUES (%s) RETURNING id",
        (nombre_equipo,)
    )
    new_id = cur.fetchone()[0]
    print(f"   -> Equipo creado: {nombre_equipo} (id={new_id})")
    return new_id


def obtener_o_crear_contrato(cur, codigo):
    codigo = codigo.strip()

    # Separar numero-vigencia
    try:
        numero_str, vigencia_str = codigo.split('-')
        numero = int(numero_str)
        vigencia = int(vigencia_str)
    except:
        print(f"   !! Error formato contrato: {codigo}")
        return None

    # Buscar contrato
    cur.execute("SELECT id FROM contrato WHERE codigo=%s", (codigo,))
    row = cur.fetchone()
    if row:
        return row[0]

    # Crear contrato
    cur.execute("""
        INSERT INTO contrato (numero, vigencia, codigo)
        VALUES (%s, %s, %s)
        RETURNING id
    """, (numero, vigencia, codigo))

    contrato_id = cur.fetchone()[0]
    print(f"   -> Contrato creado: {codigo} (id={contrato_id})")
    return contrato_id


def crear_relacion_contrato(cur, colaborador_id, contrato_id):
    """
    Crea la relación colaborador-contrato si no existe.
    """
    cur.execute("""
        SELECT id 
        FROM colaborador_contrato 
        WHERE colaborador_id=%s AND contrato_id=%s
    """, (colaborador_id, contrato_id))

    if cur.fetchone():
        print("   -> Relación ya existía (no se duplica)")
        return

    cur.execute("""
        INSERT INTO colaborador_contrato (colaborador_id, contrato_id)
        VALUES (%s, %s)
    """, (colaborador_id, contrato_id))

    print("   -> Relación colaborador–contrato creada")


# -----------------------------------------------------------
# ETL Principal
# -----------------------------------------------------------
def cargar_contratistas():
    print("="*60)
    print(" INICIO ETL CONTRATISTAS (Con contratos múltiples)")
    print("="*60)

    df = pd.read_excel(EXCEL_FILE, sheet_name=SHEET_NAME)
    df.columns = [c.strip().upper() for c in df.columns]

    required = {"CEDULA", "NOMBRE CONTRATISTA", "EQUIPO", "CONTRATO"}
    if not required.issubset(df.columns):
        print("ERROR: Faltan columnas requeridas")
        return

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    insertados = 0
    relaciones = 0
    omitidos = 0

    for i, row in df.iterrows():
        ced = str(row["CEDULA"]).strip()
        nom = str(row["NOMBRE CONTRATISTA"]).strip()
        equ = str(row["EQUIPO"]).strip()
        cod_contrato = str(row["CONTRATO"]).strip()

        print("-"*50)
        print(f"Fila {i+1} – Cédula: {ced} – Contrato: {cod_contrato}")

        if not ced.isdigit():
            print("   !! Cédula inválida")
            omitidos += 1
            continue

        # Revisar si existe colaborador
        cur.execute("SELECT id FROM colaborador WHERE cedula=%s", (ced,))
        row_col = cur.fetchone()

        if row_col:
            colaborador_id = row_col[0]
            print(f"   -> Colaborador EXISTE (id={colaborador_id})")
        else:
            # Crear colaborador nuevo
            equipo_id = obtener_o_crear_equipo(cur, equ)

            cur.execute("""
                INSERT INTO colaborador (cedula, nombre, tipo_vinculacion, perfil, equipo_id)
                VALUES (%s, %s, 'Contratista', 'Pendiente', %s)
                RETURNING id
            """, (ced, nom, equipo_id))

            colaborador_id = cur.fetchone()[0]
            print(f"   -> Colaborador creado (id={colaborador_id})")
            insertados += 1

        # Obtener/crear contrato
        contrato_id = obtener_o_crear_contrato(cur, cod_contrato)
        if not contrato_id:
            print("   !! Contrato inválido, omitido")
            omitidos += 1
            continue

        # Crear relación colaborador–contrato
        crear_relacion_contrato(cur, colaborador_id, contrato_id)
        relaciones += 1

    conn.commit()
    cur.close()
    conn.close()

    print("\n===== RESUMEN =====")
    print("Colaboradores insertados:", insertados)
    print("Relaciones creadas:", relaciones)
    print("Omitidos:", omitidos)
    print("===================")


if __name__ == "__main__":
    cargar_contratistas()
