from django.contrib import admin
from django.urls import path

# IMPORTA TODAS LAS VISTAS NECESARIAS
from gestion.views import (
    home,
    sql_runner,
    dashboard,
    colaboradores_por_equipo,
    colaborador_detalle,   # ← ESTA FALTABA
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('sql/', sql_runner, name='sql_runner'),
    path('dashboard/', dashboard, name='dashboard'),

    # Vista de colaboradores por equipo
    path('equipo/<str:equipo_nombre>/', colaboradores_por_equipo, name='colaboradores_por_equipo'),

    # Vista de detalle por colaborador
    path("colaborador/<int:colaborador_id>/", colaborador_detalle, name="colaborador_detalle"),
]
