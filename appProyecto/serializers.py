from rest_framework import serializers
from .models import (
    Usuario,
    Categoria,
    Ubicacion,
    Denuncia,
    HistorialDenuncia,
    LogActividad,
    Mensaje,
    Observacion,
    Dispositivo,
    Reporte,
    TokenRecuperacion
)


class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'rol', 'telefono', 'activo', 'date_joined']
        read_only_fields = ['id', 'date_joined']


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = '__all__'


class UbicacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ubicacion
        fields = '__all__'
        read_only_fields = ['id', 'fecha_registro']


class DenunciaSerializer(serializers.ModelSerializer):
    usuario_username = serializers.CharField(source='usuario.username', read_only=True)
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True, allow_null=True)
    ubicacion_coords = serializers.SerializerMethodField()
    
    class Meta:
        model = Denuncia
        fields = [
            'id', 
            'usuario', 
            'usuario_username', 
            'categoria', 
            'categoria_nombre',
            'ubicacion', 
            'ubicacion_coords',
            'titulo', 
            'descripcion', 
            'evidencia_url', 
            'estado',
            'prioridad', 
            'fecha_creacion', 
            'fecha_actualizacion'
        ]
        read_only_fields = ['id', 'fecha_creacion', 'fecha_actualizacion']
    
    def get_ubicacion_coords(self, obj):
        if obj.ubicacion:
            return {
                'latitud': float(obj.ubicacion.latitud),
                'longitud': float(obj.ubicacion.longitud)
            }
        return None


class HistorialDenunciaSerializer(serializers.ModelSerializer):
    usuario_username = serializers.CharField(source='usuario.username', read_only=True, allow_null=True)
    denuncia_titulo = serializers.CharField(source='denuncia.titulo', read_only=True)
    
    class Meta:
        model = HistorialDenuncia
        fields = '__all__'
        read_only_fields = ['id', 'fecha']


class LogActividadSerializer(serializers.ModelSerializer):
    usuario_username = serializers.CharField(source='usuario.username', read_only=True, allow_null=True)
    
    class Meta:
        model = LogActividad
        fields = '__all__'
        read_only_fields = ['id', 'fecha']


class MensajeSerializer(serializers.ModelSerializer):
    emisor_username = serializers.CharField(source='emisor.username', read_only=True)
    receptor_username = serializers.CharField(source='receptor.username', read_only=True)
    
    class Meta:
        model = Mensaje
        fields = '__all__'
        read_only_fields = ['id', 'fecha']


class ObservacionSerializer(serializers.ModelSerializer):
    usuario_username = serializers.CharField(source='usuario.username', read_only=True)
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True, allow_null=True)
    
    class Meta:
        model = Observacion
        fields = '__all__'
        read_only_fields = ['id', 'fecha_creacion']


class DispositivoSerializer(serializers.ModelSerializer):
    usuario_username = serializers.CharField(source='usuario.username', read_only=True)
    
    class Meta:
        model = Dispositivo
        fields = '__all__'
        read_only_fields = ['id', 'fecha_sincronizacion']


class ReporteSerializer(serializers.ModelSerializer):
    usuario_username = serializers.CharField(source='usuario.username', read_only=True, allow_null=True)
    
    class Meta:
        model = Reporte
        fields = '__all__'
        read_only_fields = ['id', 'fecha_creacion']


class TokenRecuperacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TokenRecuperacion
        fields = ['id', 'usuario', 'usado', 'fecha_creacion', 'fecha_expiracion']
        read_only_fields = ['id', 'fecha_creacion']
