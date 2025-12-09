from django.db import models


# ====================================================
#   MODELO: EQUIPO
# ====================================================
class Equipo(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = 'equipo'

    def __str__(self):
        return self.nombre


# ====================================================
#   MODELO: COLABORADOR  (SIN vinculacion_actual)
# ====================================================
class Colaborador(models.Model):

    TIPO_VINCULACION_CHOICES = [
        ("Planta", "Planta"),
        ("Contratista", "Contratista"),
        ("Operador", "Operador"),
    ]

    nombre = models.CharField(max_length=255)
    tipo_vinculacion = models.CharField(max_length=50, choices=TIPO_VINCULACION_CHOICES)
    perfil = models.TextField(null=True)
    cedula = models.CharField(max_length=20, unique=True)
    equipo = models.ForeignKey(Equipo, on_delete=models.SET_NULL, null=True)

    # Campo real existente en la DB
    estado = models.CharField(max_length=20, default="Activo")

    class Meta:
        db_table = 'colaborador'

    def __str__(self):
        return self.nombre


# ====================================================
#   MODELO: PROCEDIMIENTO
# ====================================================
class Procedimiento(models.Model):
    nombre = models.CharField(max_length=255, unique=True)

    class Meta:
        db_table = 'procedimiento'

    def __str__(self):
        return self.nombre


# ====================================================
#   MODELO: ACTIVIDAD
# ====================================================
class Actividad(models.Model):
    colaborador = models.ForeignKey(Colaborador, on_delete=models.CASCADE)
    descripcion = models.TextField()
    frecuencia = models.CharField(max_length=50)

    # En la DB actual NO existe procedimiento_id
    # → Solo existe si se recrea la vista luego, pero no está en la tabla real

    class Meta:
        db_table = 'actividad'

    def __str__(self):
        return f"{self.colaborador.nombre} – {self.descripcion[:30]}"


# ====================================================
#   MODELO: PROYECTO
# ====================================================
class Proyecto(models.Model):
    nombre = models.CharField(max_length=255)
    colaborador = models.ForeignKey(Colaborador, on_delete=models.CASCADE)

    class Meta:
        db_table = 'proyecto'

    def __str__(self):
        return self.nombre


# ====================================================
#   MODELO: ARTICULACION
# ====================================================
class Articulacion(models.Model):
    colaborador = models.ForeignKey(Colaborador, on_delete=models.CASCADE)
    entidad = models.CharField(max_length=255)
    tema = models.TextField()

    class Meta:
        db_table = 'articulacion'

    def __str__(self):
        return f"{self.entidad} – {self.tema[:30]}"


# ====================================================
#   MODELO: CONTRATO
# ====================================================
class Contrato(models.Model):
    numero = models.IntegerField()
    vigencia = models.IntegerField()
    codigo = models.CharField(max_length=50, unique=True, null=True)
    fecha_inicio = models.DateField(null=True)
    fecha_fin = models.DateField(null=True)
    valor = models.DecimalField(max_digits=14, decimal_places=2, null=True)
    objeto = models.TextField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'contrato'

    def __str__(self):
        return f"{self.codigo or self.numero}/{self.vigencia}"


# ====================================================
#   MODELO: COLABORADOR - CONTRATO
# ====================================================
class ColaboradorContrato(models.Model):
    colaborador = models.ForeignKey(Colaborador, on_delete=models.CASCADE)
    contrato = models.ForeignKey(Contrato, on_delete=models.CASCADE)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'colaborador_contrato'

    def __str__(self):
        return f"{self.colaborador.nombre} - {self.contrato}"
