from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count
from .models import (
    Usuario,
    TokenRecuperacion,
    Ubicacion,
    Categoria,
    Denuncia,
    HistorialDenuncia,
    LogActividad,
    Mensaje,
    Observacion,
    Dispositivo,
    Reporte
)


# ==============================================================================
# CONFIGURACIÓN DEL ADMIN SITE
# ==============================================================================

admin.site.site_header = "🌿 SilvaSentinel - Administración"
admin.site.site_title = "SilvaSentinel Admin"
admin.site.index_title = "Panel de Control"


# ==============================================================================
# USUARIO ADMIN
# ==============================================================================

@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    """
    Administración avanzada de usuarios con estadísticas
    """
    list_display = (
        'username',
        'email',
        'get_nombre_completo',
        'rol_badge',
        'activo_badge',
        'total_denuncias',
        'date_joined'
    )
    list_filter = ('rol', 'activo', 'is_staff', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'telefono')
    ordering = ('-date_joined',)
    
    fieldsets = (
        ('Credenciales', {
            'fields': ('username', 'password')
        }),
        ('Información Personal', {
            'fields': ('first_name', 'last_name', 'email', 'telefono')
        }),
        ('Permisos y Roles', {
            'fields': ('rol', 'activo', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Fechas Importantes', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        ('Crear Nuevo Usuario', {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'rol', 'telefono', 'activo'),
        }),
    )
    
    readonly_fields = ('last_login', 'date_joined')
    
    # Campos personalizados
    def get_nombre_completo(self, obj):
        """Mostrar nombre completo"""
        if obj.first_name or obj.last_name:
            return f"{obj.first_name} {obj.last_name}".strip()
        return "-"
    get_nombre_completo.short_description = "Nombre Completo"
    
    def rol_badge(self, obj):
        """Badge colorido para el rol"""
        colors = {
            'admin': '#dc3545',
            'revisor': '#ffc107',
            'usuario': '#0d6efd'
        }
        color = colors.get(obj.rol, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 12px; font-weight: bold;">{}</span>',
            color,
            obj.get_rol_display()
        )
    rol_badge.short_description = "Rol"
    
    def activo_badge(self, obj):
        """Badge para estado activo/inactivo"""
        if obj.activo:
            return format_html('<span style="color: green; font-weight: bold;">✅ Activo</span>')
        return format_html('<span style="color: red; font-weight: bold;">❌ Inactivo</span>')
    activo_badge.short_description = "Estado"
    
    def total_denuncias(self, obj):
        """Contar denuncias del usuario"""
        count = obj.denuncias.count()
        if count > 0:
            url = reverse('admin:appProyecto_denuncia_changelist') + f'?usuario__id__exact={obj.id}'
            return format_html('<a href="{}" style="font-weight: bold;">{} denuncias</a>', url, count)
        return "0 denuncias"
    total_denuncias.short_description = "Denuncias"


# ==============================================================================
# CATEGORÍA ADMIN
# ==============================================================================

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    """
    Administración de categorías con contador de denuncias
    """
    list_display = ('nombre', 'slug', 'total_denuncias', 'descripcion_corta')
    search_fields = ('nombre', 'descripcion')
    prepopulated_fields = {'slug': ('nombre',)}
    ordering = ('nombre',)
    
    def total_denuncias(self, obj):
        """Contar denuncias por categoría"""
        count = obj.denuncias.count()
        if count > 0:
            url = reverse('admin:appProyecto_denuncia_changelist') + f'?categoria__id__exact={obj.id}'
            return format_html('<a href="{}" style="font-weight: bold;">{}</a>', url, count)
        return "0"
    total_denuncias.short_description = "Total Denuncias"
    
    def descripcion_corta(self, obj):
        """Mostrar descripción resumida"""
        if obj.descripcion:
            return obj.descripcion[:50] + "..." if len(obj.descripcion) > 50 else obj.descripcion
        return "-"
    descripcion_corta.short_description = "Descripción"


# ==============================================================================
# UBICACIÓN ADMIN
# ==============================================================================

@admin.register(Ubicacion)
class UbicacionAdmin(admin.ModelAdmin):
    """
    Administración de ubicaciones con mapa
    """
    list_display = ('id', 'descripcion_corta', 'coordenadas', 'fecha_registro')
    list_filter = ('fecha_registro',)
    search_fields = ('descripcion',)
    readonly_fields = ('fecha_registro',)
    ordering = ('-fecha_registro',)
    
    def descripcion_corta(self, obj):
        """Descripción resumida"""
        if obj.descripcion:
            return obj.descripcion[:40] + "..." if len(obj.descripcion) > 40 else obj.descripcion
        return "Sin descripción"
    descripcion_corta.short_description = "Ubicación"
    
    def coordenadas(self, obj):
        """Mostrar coordenadas con link a Google Maps"""
        if obj.latitud and obj.longitud:
            maps_url = f"https://www.google.com/maps?q={obj.latitud},{obj.longitud}"
            return format_html(
                '<a href="{}" target="_blank" style="color: #0d6efd;">📍 {}, {}</a>',
                maps_url,
                obj.latitud,
                obj.longitud
            )
        return "-"
    coordenadas.short_description = "GPS"


# ==============================================================================
# DENUNCIA ADMIN
# ==============================================================================

@admin.register(Denuncia)
class DenunciaAdmin(admin.ModelAdmin):
    """
    Administración avanzada de denuncias
    """
    list_display = (
        'id',
        'titulo_corto',
        'usuario',
        'categoria',
        'estado_badge',
        'prioridad_badge',
        'evidencia_icon',
        'fecha_creacion'
    )
    list_filter = ('estado', 'prioridad', 'categoria', 'fecha_creacion')
    search_fields = ('titulo', 'descripcion', 'usuario__username')
    date_hierarchy = 'fecha_creacion'
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')
    ordering = ('-fecha_creacion',)
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('usuario', 'categoria', 'titulo', 'descripcion')
        }),
        ('Ubicación', {
            'fields': ('ubicacion',),
            'classes': ('collapse',)
        }),
        ('Evidencia', {
            'fields': ('evidencia', 'evidencia_url'),
            'classes': ('collapse',)
        }),
        ('Gestión', {
            'fields': ('estado', 'prioridad')
        }),
        ('Fechas', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )
    
    def titulo_corto(self, obj):
        """Mostrar título resumido con link"""
        titulo = obj.titulo[:50] + "..." if len(obj.titulo) > 50 else obj.titulo
        url = reverse('admin:appProyecto_denuncia_change', args=[obj.id])
        return format_html('<a href="{}" style="font-weight: bold;">{}</a>', url, titulo)
    titulo_corto.short_description = "Título"
    
    def estado_badge(self, obj):
        """Badge colorido para estado"""
        colors = {
            'pendiente': '#ffc107',
            'en_proceso': '#0dcaf0',
            'resuelta': '#198754',
            'rechazada': '#dc3545'
        }
        color = colors.get(obj.estado, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_estado_display()
        )
    estado_badge.short_description = "Estado"
    
    def prioridad_badge(self, obj):
        """Badge para prioridad"""
        colors = {
            'alta': '#dc3545',
            'media': '#ffc107',
            'baja': '#198754'
        }
        icons = {
            'alta': '🔴',
            'media': '🟡',
            'baja': '🟢'
        }
        color = colors.get(obj.prioridad, '#6c757d')
        icon = icons.get(obj.prioridad, '⚪')
        return format_html(
            '{} <span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 10px; font-size: 10px;">{}</span>',
            icon,
            color,
            obj.get_prioridad_display()
        )
    prioridad_badge.short_description = "Prioridad"
    
    def evidencia_icon(self, obj):
        """Icono de evidencia"""
        if obj.evidencia:
            return format_html('<span style="color: green; font-size: 18px;" title="Tiene archivo">📎</span>')
        elif obj.evidencia_url:
            return format_html('<span style="color: blue; font-size: 18px;" title="Tiene URL">🔗</span>')
        return format_html('<span style="color: gray; font-size: 18px;" title="Sin evidencia">❌</span>')
    evidencia_icon.short_description = "Evidencia"


# ==============================================================================
# HISTORIAL DENUNCIA ADMIN
# ==============================================================================

@admin.register(HistorialDenuncia)
class HistorialDenunciaAdmin(admin.ModelAdmin):
    """
    Historial de cambios en denuncias
    """
    list_display = ('denuncia', 'usuario', 'tipo_accion_badge', 'cambio_descripcion_corta', 'fecha')
    list_filter = ('tipo_accion', 'fecha')
    search_fields = ('denuncia__titulo', 'usuario__username', 'cambio_descripcion')
    date_hierarchy = 'fecha'
    readonly_fields = ('fecha',)
    ordering = ('-fecha',)
    
    def tipo_accion_badge(self, obj):
        """Badge para tipo de acción"""
        colors = {
            'creacion': '#198754',
            'edicion': '#0dcaf0',
            'cambio_estado': '#ffc107',
            'asignacion': '#0d6efd'
        }
        color = colors.get(obj.tipo_accion, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 8px; font-size: 11px;">{}</span>',
            color,
            obj.get_tipo_accion_display()
        )
    tipo_accion_badge.short_description = "Acción"
    
    def cambio_descripcion_corta(self, obj):
        """Descripción resumida del cambio"""
        if obj.cambio_descripcion:
            return obj.cambio_descripcion[:60] + "..." if len(obj.cambio_descripcion) > 60 else obj.cambio_descripcion
        return "-"
    cambio_descripcion_corta.short_description = "Cambio"


# ==============================================================================
# LOG ACTIVIDAD ADMIN
# ==============================================================================

@admin.register(LogActividad)
class LogActividadAdmin(admin.ModelAdmin):
    """
    Registro de actividades del sistema
    """
    list_display = ('usuario', 'accion_corta', 'ip_origen', 'fecha')
    list_filter = ('fecha',)
    search_fields = ('usuario__username', 'accion', 'ip_origen')
    date_hierarchy = 'fecha'
    readonly_fields = ('fecha',)
    ordering = ('-fecha',)
    
    def accion_corta(self, obj):
        """Acción resumida"""
        return obj.accion[:80] + "..." if len(obj.accion) > 80 else obj.accion
    accion_corta.short_description = "Acción"


# ==============================================================================
# MENSAJE ADMIN
# ==============================================================================

@admin.register(Mensaje)
class MensajeAdmin(admin.ModelAdmin):
    """
    Gestión de mensajes entre usuarios
    """
    list_display = ('emisor', 'receptor', 'asunto_corto', 'leido_badge', 'fecha')
    list_filter = ('leido', 'fecha')
    search_fields = ('emisor__username', 'receptor__username', 'asunto', 'contenido')
    date_hierarchy = 'fecha'
    readonly_fields = ('fecha',)
    ordering = ('-fecha',)
    
    def asunto_corto(self, obj):
        """Asunto resumido"""
        return obj.asunto[:50] + "..." if len(obj.asunto) > 50 else obj.asunto
    asunto_corto.short_description = "Asunto"
    
    def leido_badge(self, obj):
        """Badge de lectura"""
        if obj.leido:
            return format_html('<span style="color: green;">✅ Leído</span>')
        return format_html('<span style="color: red; font-weight: bold;">📧 No leído</span>')
    leido_badge.short_description = "Estado"


# ==============================================================================
# OBSERVACIÓN ADMIN
# ==============================================================================

@admin.register(Observacion)
class ObservacionAdmin(admin.ModelAdmin):
    """
    Observaciones en denuncias
    """
    list_display = ('titulo_corto', 'usuario', 'fecha_creacion')
    list_filter = ('fecha_creacion',)
    search_fields = ('titulo', 'descripcion', 'usuario__username')
    date_hierarchy = 'fecha_creacion'
    readonly_fields = ('fecha_creacion',)
    ordering = ('-fecha_creacion',)
    
    def titulo_corto(self, obj):
        """Título resumido"""
        return obj.titulo[:60] + "..." if len(obj.titulo) > 60 else obj.titulo
    titulo_corto.short_description = "Observación"


# ==============================================================================
# DISPOSITIVO ADMIN
# ==============================================================================

@admin.register(Dispositivo)
class DispositivoAdmin(admin.ModelAdmin):
    """
    Dispositivos registrados
    """
    list_display = ('identificador', 'tipo_badge', 'usuario',)
    list_filter = ('tipo',)
    search_fields = ('identificador', 'usuario__username')
    
    def tipo_badge(self, obj):
        """Badge para tipo de dispositivo"""
        icons = {
            'web': '💻',
            'movil': '📱',
            'tablet': '📋'
        }
        icon = icons.get(obj.tipo, '🔧')
        return format_html('{} {}', icon, obj.get_tipo_display())
    tipo_badge.short_description = "Tipo"
    


# ==============================================================================
# REPORTE ADMIN
# ==============================================================================

@admin.register(Reporte)
class ReporteAdmin(admin.ModelAdmin):
    """
    Reportes generados
    """
    list_display = ('titulo', 'usuario', 'fecha_creacion')
    list_filter = ('fecha_creacion',)
    search_fields = ('titulo', 'usuario__username')
    date_hierarchy = 'fecha_creacion'
    readonly_fields = ('fecha_creacion',)
    ordering = ('-fecha_creacion',)


# ==============================================================================
# TOKEN RECUPERACIÓN ADMIN
# ==============================================================================

@admin.register(TokenRecuperacion)
class TokenRecuperacionAdmin(admin.ModelAdmin):
    """
    Tokens de recuperación de contraseña
    """
    list_display = ('usuario', 'usado_badge', 'fecha_creacion', 'fecha_expiracion', 'estado_token')
    list_filter = ('usado', 'fecha_creacion', 'fecha_expiracion')
    search_fields = ('usuario__username', 'token')
    readonly_fields = ('fecha_creacion',)
    ordering = ('-fecha_creacion',)
    
    def usado_badge(self, obj):
        """Badge de uso"""
        if obj.usado:
            return format_html('<span style="color: gray;">✅ Usado</span>')
        return format_html('<span style="color: green; font-weight: bold;">🔓 Disponible</span>')
    usado_badge.short_description = "Estado"
    
    def estado_token(self, obj):
        """Estado de validez del token"""
        from django.utils import timezone
        if obj.usado:
            return format_html('<span style="color: gray;">Usado</span>')
        elif timezone.now() > obj.fecha_expiracion:
            return format_html('<span style="color: red;">⏰ Expirado</span>')
        return format_html('<span style="color: green;">✅ Válido</span>')
    estado_token.short_description = "Validez"
