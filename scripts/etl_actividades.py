import pandas as pd
from sqlalchemy import create_engine, text
import re

# ========================================
# CONFIGURACIÓN BD + ARCHIVO
# ========================================
DATABASE_URL = "postgresql://postgres:Alejito10.@localhost/srni_actividades"
engine = create_engine(DATABASE_URL)

EXCEL_FILE = "data/Actividades colaboradores SRNI (2).xlsx"

# HOJAS A PROCESAR
SHEETS = ["EQUIPO BASE", "PROCEDIMIENTOS"]

# ========================================
# CATÁLOGO DE FRECUENCIAS
# ========================================
CATALOGO_FRECUENCIAS = {
    "diaria": "Diaria",
    "diario": "Diaria",
    "día": "Diaria",
    "semanal": "Semanal",
    "mensual": "Mensual",
    "trimestral": "Trimestral",
    "semestral": "Semestral",
    "quincenal": "Quincenal",
    "a demanda": "A demanda",
    "ademanda": "A demanda",
    "una vez": "Una vez",
    "anual": "Anual",
}

def normalizar_frecuencia(texto):
    if not isinstance(texto, str):
        return "A demanda"
    t = texto.strip().lower()
    for key, val in CATALOGO_FRECUENCIAS.items():
        if key in t:
            return val
    return "A demanda"


# ========================================
# LIMPIEZA DE TEXTO
# ========================================
def limpiar_texto(texto):
    """Elimina numeración como '1.' o '2)' al inicio."""
    if not isinstance(texto, str):
        return ""
    texto = texto.strip()
    texto = re.sub(r"^\s*\d+[\.\)]\s*", "", texto)
    return texto


def separar_lineas(texto):
    """Divide un texto multilínea en líneas limpias sin vacíos."""
    if not isinstance(texto, str):
        return []
    partes = [limpiar_texto(p) for p in texto.split("\n")]
    return [p for p in partes if p.strip()]


# ========================================
# ETL PRINCIPAL
# ========================================
def run_etl():

    print("\n=== LEYENDO EXCEL ===")
    print(f"Procesando hojas: {SHEETS}")

    with engine.begin() as conn:

        print("\nEliminando actividades previas…")
        conn.execute(text("DELETE FROM actividad;"))

        for sheet in SHEETS:
            print(f"\n==============================")
            print(f"   HOJA: {sheet}")
            print(f"==============================")

            df = pd.read_excel(EXCEL_FILE, sheet_name=sheet)

            df.columns = [c.strip().upper() for c in df.columns]

            # Validar que existan las columnas necesarias
            required = {
                "NO DOCUMENTO IDENTIDAD",
                "NOMBRE COLABORADOR",
                "ACTIVIDADES QUE DESARROLLA (DESCRIBA UNA A UNA)",
                "FRECUENCIA DE CADA ACTIVIDAD (DIARIA / SEMANAL / MENSUAL / TRIMESTRAL, OTRA ¿CUÁL?)",
            }

            if not required.issubset(df.columns):
                print(f"⚠️  La hoja {sheet} NO contiene las columnas necesarias. Se omite.")
                continue

            for idx, row in df.iterrows():

                cedula_raw = row["NO DOCUMENTO IDENTIDAD"]
                cedula = str(cedula_raw).replace(",", "").replace(".0", "").strip()

                nombre = row["NOMBRE COLABORADOR"]

                actividades_raw = row["ACTIVIDADES QUE DESARROLLA (DESCRIBA UNA A UNA)"]
                frecuencias_raw = row["FRECUENCIA DE CADA ACTIVIDAD (DIARIA / SEMANAL / MENSUAL / TRIMESTRAL, OTRA ¿CUÁL?)"]

                print("\n---------------------------------------------")
                print(f"Fila {idx+1} → {nombre}  ({cedula})")

                # Buscar colaborador
                result = conn.execute(
                    text("SELECT id FROM colaborador WHERE cedula = :c"),
                    {"c": cedula}
                ).fetchone()

                if not result:
                    print(f"❌ Colaborador con cédula {cedula} NO existe → se omite.")
                    continue

                colaborador_id = result[0]
                print(f"✔ Colaborador encontrado (id={colaborador_id})")

                # Separar listas
                actividades = separar_lineas(actividades_raw)
                frecuencias = separar_lineas(frecuencias_raw)

                print(f"   Actividades detectadas: {len(actividades)}")
                print(f"   Frecuencias detectadas: {len(frecuencias)}")

                # Alinear frecuencias
                if len(frecuencias) < len(actividades):
                    faltan = len(actividades) - len(frecuencias)
                    frecuencias += ["A demanda"] * faltan

                # Insertar actividades
                for act, freq in zip(actividades, frecuencias):
                    freq_norm = normalizar_frecuencia(freq)

                    conn.execute(
                        text("""
                            INSERT INTO actividad (colaborador_id, descripcion, frecuencia)
                            VALUES (:cid, :desc, :freq)
                        """),
                        {
                            "cid": colaborador_id,
                            "desc": act,
                            "freq": freq_norm
                        }
                    )

                    print(f"   ✔ '{act}' – Frecuencia: {freq_norm}")

    print("\nETL COMPLETADO.\n")


# ---------------------------------------------
# RUN
# ---------------------------------------------
if __name__ == "__main__":
    run_etl()
