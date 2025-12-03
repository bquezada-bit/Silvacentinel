from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from decimal import Decimal


class Usuario(AbstractUser):

    ROLES = (
        ('usuario', 'Usuario Público'),
        ('revisor', 'Revisor'),
        ('admin', 'Administrador'),
    )
    
    rol = models.CharField(
        max_length=20,
        choices=ROLES,
        default='usuario',
        help_text='Rol del usuario en el sistema'
    )
    telefono = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text='Teléfono de contacto'
    )
    activo = models.BooleanField(
        default=True,
        help_text='Indica si la cuenta está activa'
    )
    
    class Meta:
        db_table = 'usuarios'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['-date_joined']
    
    def __str__(self):
        return f"{self.username} ({self.get_rol_display()})"
    
    def es_admin(self):
        return self.rol == 'admin'
    
    def es_revisor(self):
        return self.rol == 'revisor'
    
    def puede_modificar_denuncias(self):
        return self.rol in ['admin', 'revisor']
    
    def puede_gestionar_usuarios(self):
        return self.rol == 'admin'



class TokenRecuperacion(models.Model):

    
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='tokens_recuperacion',
        help_text='Usuario que solicitó recuperación'
    )
    token = models.CharField(
        max_length=255,
        unique=True,
        help_text='Token único generado'
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        help_text='Fecha de creación del token'
    )
    fecha_expiracion = models.DateTimeField(
        help_text='Fecha de expiración (24h desde creación)'
    )
    usado = models.BooleanField(
        default=False,
        help_text='Indica si el token ya fue usado'
    )
    
    class Meta:
        db_table = 'tokens_recuperacion'
        verbose_name = 'Token de Recuperación'
        verbose_name_plural = 'Tokens de Recuperación'
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"Token para {self.usuario.username} - {'Usado' if self.usado else 'Activo'}"
    
    def esta_vigente(self):
        return not self.usado and timezone.now() < self.fecha_expiracion



class Ubicacion(models.Model):
    
    latitud = models.DecimalField(
        max_digits=10,
        decimal_places=8,
        help_text='Latitud GPS'
    )
    longitud = models.DecimalField(
        max_digits=11,
        decimal_places=8,
        help_text='Longitud GPS'
    )
    altitud = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
        help_text='Altitud en metros sobre el nivel del mar'
    )
    descripcion = models.TextField(
        blank=True,
        null=True,
        help_text='Descripción textual del lugar'
    )
    fecha_registro = models.DateTimeField(
        auto_now_add=True,
        help_text='Fecha de registro de la ubicación'
    )
    
    class Meta:
        db_table = 'ubicaciones'
        verbose_name = 'Ubicación'
        verbose_name_plural = 'Ubicaciones'
        ordering = ['-fecha_registro']
    
    def __str__(self):
        return f"Lat: {self.latitud}, Lon: {self.longitud}"
    
    def coordenadas_str(self):
        return f"{self.latitud}, {self.longitud}"


class Categoria(models.Model):
    
    nombre = models.CharField(
        max_length=100,
        unique=True,
        help_text='Nombre de la categoría'
    )
    slug = models.SlugField(
        max_length=50,
        unique=True,
        help_text='Identificador único (ej: flora, fauna, contaminacion)'
    )
    descripcion = models.TextField(
        blank=True,
        null=True,
        help_text='Descripción de la categoría'
    )
    
    class Meta:
        db_table = 'categorias'
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre


class Denuncia(models.Model):
    ESTADOS = (
        ('pendiente', 'Pendiente'),
        ('en_proceso', 'En Proceso'),
        ('resuelta', 'Resuelta'),
        ('rechazada', 'Rechazada'),
    )
    
    PRIORIDADES = (
        ('baja', 'Baja'),
        ('media', 'Media'),
        ('alta', 'Alta'),
    )
    
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='denuncias',
        help_text='Usuario que creó la denuncia'
    )
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='denuncias',
        help_text='Categoría de la denuncia'
    )
    ubicacion = models.ForeignKey(
        Ubicacion,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='denuncias',
        help_text='Ubicación GPS del incidente'
    )
    
    titulo = models.CharField(
        max_length=150,
        help_text='Título breve de la denuncia'
    )
    descripcion = models.TextField(
        help_text='Descripción detallada del problema'
    )
    
    evidencia = models.FileField(
        upload_to='evidencias/%Y/%m/%d/',
        blank=True,
        null=True,
        help_text='Archivo de evidencia (imagen o video)'
    )
    
    evidencia_url = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='URL alternativa de evidencia'
    )
    
    estado = models.CharField(
        max_length=50,
        choices=ESTADOS,
        default='pendiente',
        help_text='Estado actual de la denuncia'
    )
    prioridad = models.CharField(
        max_length=20,
        choices=PRIORIDADES,
        default='media',
        help_text='Nivel de prioridad'
    )
    
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        help_text='Fecha de creación'
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        help_text='Última actualización'
    )
    
    class Meta:
        db_table = 'denuncias'
        verbose_name = 'Denuncia'
        verbose_name_plural = 'Denuncias'
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"{self.titulo} - {self.get_estado_display()}"
    
    def puede_editar(self, usuario):
        return usuario.puede_modificar_denuncias() or usuario == self.usuario
    
    def tiene_evidencia(self):
        return bool(self.evidencia or self.evidencia_url)



class HistorialDenuncia(models.Model):
    
    TIPOS_ACCION = (
        ('creacion', 'Creación'),
        ('edicion', 'Edición'),
        ('cambio_estado', 'Cambio de Estado'),
        ('comentario', 'Comentario'),
        ('asignacion', 'Asignación'),
    )
    
    denuncia = models.ForeignKey(
        Denuncia,
        on_delete=models.CASCADE,
        related_name='historial',
        help_text='Denuncia afectada'
    )
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='acciones_denuncias',
        help_text='Usuario que realizó la acción'
    )
    tipo_accion = models.CharField(
        max_length=50,
        choices=TIPOS_ACCION,
        help_text='Tipo de acción realizada'
    )
    cambio_descripcion = models.TextField(
        blank=True,
        null=True,
        help_text='Descripción detallada del cambio'
    )
    fecha = models.DateTimeField(
        auto_now_add=True,
        help_text='Fecha de la acción'
    )
    
    class Meta:
        db_table = 'historial_denuncias'
        verbose_name = 'Historial de Denuncia'
        verbose_name_plural = 'Historial de Denuncias'
        ordering = ['-fecha']
    
    def __str__(self):
        return f"{self.get_tipo_accion_display()} - {self.denuncia.titulo}"


class LogActividad(models.Model):
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='logs_actividad',
        help_text='Usuario que realizó la acción'
    )
    accion = models.CharField(
        max_length=255,
        help_text='Descripción de la acción realizada'
    )
    ip_origen = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text='Dirección IP del usuario'
    )
    fecha = models.DateTimeField(
        auto_now_add=True,
        help_text='Fecha y hora de la acción'
    )
    
    class Meta:
        db_table = 'logs_actividad'
        verbose_name = 'Log de Actividad'
        verbose_name_plural = 'Logs de Actividad'
        ordering = ['-fecha']
    
    def __str__(self):
        usuario_str = self.usuario.username if self.usuario else 'Anónimo'
        return f"{usuario_str} - {self.accion}"


class Mensaje(models.Model):
    emisor = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='mensajes_enviados',
        help_text='Usuario que envía el mensaje'
    )
    receptor = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='mensajes_recibidos',
        help_text='Usuario que recibe el mensaje'
    )
    contenido = models.TextField(
        help_text='Contenido del mensaje'
    )
    fecha = models.DateTimeField(
        auto_now_add=True,
        help_text='Fecha de envío'
    )
    leido = models.BooleanField(
        default=False,
        help_text='Indica si el mensaje fue leído'
    )
    
    class Meta:
        db_table = 'mensajes'
        verbose_name = 'Mensaje'
        verbose_name_plural = 'Mensajes'
        ordering = ['-fecha']
    
    def __str__(self):
        return f"De {self.emisor.username} a {self.receptor.username}"


class Observacion(models.Model):
    
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='observaciones',
        help_text='Usuario que realizó la observación'
    )
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='observaciones',
        help_text='Categoría de la observación'
    )
    ubicacion = models.ForeignKey(
        Ubicacion,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='observaciones',
        help_text='Ubicación de la observación'
    )
    titulo = models.CharField(
        max_length=150,
        help_text='Título de la observación'
    )
    descripcion = models.TextField(
        help_text='Descripción detallada'
    )
    imagen_url = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='URL de imagen'
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        help_text='Fecha de registro'
    )
    
    class Meta:
        db_table = 'observaciones'
        verbose_name = 'Observación'
        verbose_name_plural = 'Observaciones'
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"{self.titulo} - {self.usuario.username}"


class Dispositivo(models.Model):
   
    TIPOS = (
        ('camara', 'Cámara'),
        ('dron', 'Dron'),
        ('sensor', 'Sensor'),
        ('estacion_clima', 'Estación Climática'),
    )
    
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='dispositivos',
        help_text='Usuario responsable'
    )
    identificador = models.CharField(
        max_length=100,
        unique=True,
        help_text='Identificador único (serial/MAC)'
    )
    tipo = models.CharField(
        max_length=50,
        choices=TIPOS,
        help_text='Tipo de dispositivo'
    )
    ultima_ubicacion = models.ForeignKey(
        Ubicacion,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='dispositivos',
        help_text='Última ubicación registrada'
    )
    fecha_sincronizacion = models.DateTimeField(
        auto_now=True,
        help_text='Última sincronización'
    )
    
    class Meta:
        db_table = 'dispositivos'
        verbose_name = 'Dispositivo'
        verbose_name_plural = 'Dispositivos'
        ordering = ['-fecha_sincronizacion']
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.identificador}"


class Reporte(models.Model):
    
    titulo = models.CharField(
        max_length=150,
        help_text='Título del reporte'
    )
    descripcion = models.TextField(
        blank=True,
        null=True,
        help_text='Descripción del reporte'
    )
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='reportes_generados',
        help_text='Usuario que generó el reporte'
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        help_text='Fecha de generación'
    )
    archivo_url = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='URL del archivo PDF generado'
    )
    
    class Meta:
        db_table = 'reportes'
        verbose_name = 'Reporte'
        verbose_name_plural = 'Reportes'
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"{self.titulo} - {self.fecha_creacion.strftime('%d/%m/%Y')}"
