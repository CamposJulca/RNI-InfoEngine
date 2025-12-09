from django.db import connection
from django.shortcuts import render

from .models import (
    Colaborador, Actividad, Procedimiento, Proyecto,
    Articulacion, Contrato, ColaboradorContrato, Equipo
)

from django.db.models import Count, F, Sum, Q
from django.conf import settings
from datetime import date
import psycopg2


# ==============================
# CONSULTAS PREDEFINIDAS (NO EJECUTAN)
# ==============================
PREDEFINED_QUERIES = {
    "colaboradores_total": "SELECT COUNT(*) AS total_colaboradores FROM gestion_colaborador;",
    "actividades_total": "SELECT COUNT(*) AS total_actividades FROM gestion_actividad;",
    "actividades_por_vinculacion": """
        SELECT tipo_vinculacion, COUNT(*) 
        FROM gestion_colaborador 
        GROUP BY tipo_vinculacion;
    """,
    "actividades_por_procedimiento": """
        SELECT p.nombre AS procedimiento, COUNT(a.id) AS total
        FROM gestion_actividad a
        LEFT JOIN gestion_procedimiento p ON a.procedimiento_id = p.id
        GROUP BY p.nombre;
    """,
    "proyectos_por_colaborador": """
        SELECT c.nombre AS colaborador, COUNT(p.id) AS total_proyectos
        FROM gestion_proyecto p
        JOIN gestion_colaborador c ON p.colaborador_id = c.id
        GROUP BY c.nombre;
    """,
}


# ==============================
#   EJECUTOR SQL
# ==============================
def sql_runner(request):
    result = None
    error = None
    selected = None

    if request.method == "POST":

        # BOTÓN PREDEFINIDO
        predefined_key = request.POST.get("predefined")
        if predefined_key and predefined_key in PREDEFINED_QUERIES:
            selected = PREDEFINED_QUERIES[predefined_key]
            return render(request, "sql_runner.html", {
                "queries": PREDEFINED_QUERIES,
                "selected": selected,
                "result": None,
                "error": None,
            })

        # CONSULTA LIBRE
        query = request.POST.get("query", "").strip()
        selected = query

        try:
            conn = psycopg2.connect(
                dbname=settings.DATABASES['default']['NAME'],
                user=settings.DATABASES['default']['USER'],
                password=settings.DATABASES['default']['PASSWORD'],
                host=settings.DATABASES['default']['HOST'],
                port=settings.DATABASES['default']['PORT'],
            )
            cur = conn.cursor()
            cur.execute(query)

            if query.lower().startswith("select"):
                result = cur.fetchall()
            else:
                conn.commit()
                result = [["Consulta OK"]]

            cur.close()
            conn.close()

        except Exception as e:
            error = str(e)

    return render(request, "sql_runner.html", {
        "queries": PREDEFINED_QUERIES,
        "selected": selected,
        "result": result,
        "error": error,
    })


# ==============================
#   DASHBOARD MEJORADO
# ==============================

from django.db import connection
from django.shortcuts import render
from .models import Colaborador

def dashboard(request):
    # 1. TOTAL COLABORADORES ACTIVOS
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*)
            FROM vw_colaboradores_consolidado
            WHERE estado = 'Activo';
        """)
        total_activos = cursor.fetchone()[0]

    # 2. DISTRIBUCIÓN POR EQUIPO
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT equipo_nombre, COUNT(*)
            FROM vw_colaboradores_consolidado
            WHERE estado = 'Activo'
            GROUP BY equipo_nombre
            ORDER BY COUNT(*) DESC;
        """)
        rows_equipo = cursor.fetchall()

    stats_equipo = {
        "labels": [r[0] for r in rows_equipo],
        "values": [r[1] for r in rows_equipo],
    }

    # 3. DISTRIBUCIÓN POR VINCULACIÓN
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT tipo_vinculacion, COUNT(*)
            FROM vw_colaboradores_consolidado
            WHERE estado = 'Activo'
            GROUP BY tipo_vinculacion
            ORDER BY COUNT(*) DESC;
        """)
        rows_vinc = cursor.fetchall()

    stats_vinc = {
        "labels": [r[0] for r in rows_vinc],
        "values": [r[1] for r in rows_vinc],
    }

    return render(request, "dashboard.html", {
        "total_contratos": total_activos,
        "stats_equipo": stats_equipo,
        "stats_vinculacion": stats_vinc,
    })


# ==========================================================
# NUEVA VISTA: COLABORADORES POR EQUIPO
# ==========================================================
def colaboradores_por_equipo(request, equipo_nombre):

    colaboradores = Colaborador.objects.filter(
        equipo__nombre=equipo_nombre,
        estado="Activo"
    ).order_by("nombre")

    return render(request, "colaboradores_equipo.html", {
        "equipo": equipo_nombre,
        "colaboradores": colaboradores
    })

def colaborador_detalle(request, colaborador_id):

    colaborador = Colaborador.objects.filter(id=colaborador_id).first()
    actividades_raw = Actividad.objects.filter(
        colaborador_id=colaborador_id
    ).order_by("descripcion")

    # =====================================================
    # Construcción del árbol: generales → específicas
    # =====================================================
    arbol = {}
    general_actual = None

    import re
    patron_general = re.compile(r"^\d+\.$")           # "1." "2."
    patron_detalle = re.compile(r"^\d+\.\d+")         # "1.1" "2.3" etc.

    for act in actividades_raw:
        texto = act.descripcion.strip()

        if patron_general.match(texto):
            # Actividad general
            general_actual = texto
            arbol[general_actual] = []
        elif patron_detalle.match(texto):
            # Subactividad específica
            if general_actual is not None:
                arbol[general_actual].append(texto)
            else:
                # En caso raro: subactividad sin general → se crea grupo
                arbol.setdefault("Otras actividades", []).append(texto)
        else:
            # Texto normal → también es general
            general_actual = texto
            arbol[general_actual] = []

    articulaciones = Articulacion.objects.filter(colaborador_id=colaborador_id)
    proyectos = Proyecto.objects.filter(colaborador_id=colaborador_id)

    contratos = (Contrato.objects
                 .filter(colaboradorcontrato__colaborador_id=colaborador_id)
                 .order_by('-vigencia'))

    return render(request, "colaborador_detalle.html", {
        "colaborador": colaborador,
        "arbol_actividades": arbol,
        "articulaciones": articulaciones,
        "proyectos": proyectos,
        "contratos": contratos,
    })


# ==============================
#   HOME PRINCIPAL
# ==============================
def home(request):
    colaboradores = Colaborador.objects.select_related("equipo")
    actividades = Actividad.objects.select_related('colaborador', 'procedimiento')
    procedimientos = Procedimiento.objects.all()
    proyectos = Proyecto.objects.select_related('colaborador')
    articulaciones = Articulacion.objects.select_related('colaborador')

    return render(request, "home.html", {
        "colaboradores": colaboradores,
        "actividades": actividades,
        "procedimientos": procedimientos,
        "proyectos": proyectos,
        "articulaciones": articulaciones,
    })