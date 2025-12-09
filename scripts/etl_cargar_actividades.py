import pandas as pd
from django.conf import settings
from django.db import transaction
import django
import re
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "srni_web.settings")
django.setup()

from gestion.models import Colaborador, Actividad

# -------------------------------------------------------------------
# UTILIDADES
# -------------------------------------------------------------------

def limpiar_texto(texto):
    """Quita numeración como '1.' o '2)' y espacios sobrantes."""
    if not isinstance(texto, str):
        return ""
    texto = texto.strip()
    texto = re.sub(r"^\s*\d+[\.\)]\s*", "", texto)
    return texto


def separar_lineas(texto):
    """Divide en líneas limpias eliminando vacíos."""
    if not isinstance(texto, str):
        return []
    lineas = [limpiar_texto(l) for l in texto.split("\n")]
    return [l for l in lineas if l]


# -------------------------------------------------------------------
# ETL PRINCIPAL
# -------------------------------------------------------------------
def cargar_actividades_excel(ruta_excel):
    df = pd.read_excel(ruta_excel)

    print("\n========================")
    print("   ETL ACTIVIDADES SRNI")
    print("========================\n")

    for idx, row in df.iterrows():

        cedula = str(row.get("No Documento Identidad")).strip()
        actividades_raw = row.get("Actividades que desarrolla", "")
        frecuencias_raw = row.get("Frecuencia de cada actividad", "")

        print(f"\nFila {idx+1} – Cédula {cedula}")

        # Buscar colaborador
        colaborador = Colaborador.objects.filter(cedula=cedula).first()

        if not colaborador:
            print(f"   ❌ No existe colaborador con cédula {cedula}")
            continue

        print(f"   → Colaborador encontrado: {colaborador.nombre}")

        # Separar actividades y frecuencias
        actividades = separar_lineas(actividades_raw)
        frecuencias = separar_lineas(frecuencias_raw)

        print(f"   Actividades detectadas: {len(actividades)}")
        print(f"   Frecuencias detectadas: {len(frecuencias)}")

        # Alinear frecuencias al número de actividades
        if len(frecuencias) < len(actividades):
            diferencias = len(actividades) - len(frecuencias)
            frecuencias += ["Sin frecuencia"] * diferencias

        # Insertar actividades
        for act, freq in zip(actividades, frecuencias):
            actividad = Actividad.objects.create(
                colaborador=colaborador,
                descripcion=act,
                frecuencia=freq
            )
            print(f"   ✔ Insertada: '{act}' – Frecuencia: {freq}")

    print("\n=========== RESUMEN ===========")
    print(" ETL completado sin errores fatales.")
    print("================================\n")


if __name__ == "__main__":
    cargar_actividades_excel("Data/Actividades colaboradores SRNI (2).xlsx")
