from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.db.models import Count
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import requests
from django.conf import settings
from django.shortcuts import render

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

# ✅ IMPORTAR DECORADORES PERSONALIZADOS
from .decorators import rol_requerido, solo_admin, admin_o_revisor, usuario_autenticado

from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response

# ========================================
# VISTAS PÚBLICAS (sin autenticación)
# ========================================

def index(request):
    """Página principal - Acceso público"""
    from django.db.models import Count

    context = {
        'total_denuncias': Denuncia.objects.count(),
        'denuncias_resueltas': Denuncia.objects.filter(estado='resuelta').count(),
        'total_usuarios': Usuario.objects.count(),
        'categorias_count': Categoria.objects.count(),
    }

    return render(request, 'index.html', context)

def pagina1(request):
    """Quiénes somos - Acceso público"""
    return render(request, 'pagina1.html')

def pagina4(request):
    """Contáctanos - Acceso público"""
    return render(request, 'pagina4.html')

def pagina5(request):
    """Técnicas de cuidado ambiental - Acceso público"""
    return render(request, 'pagina5.html')

# ========================================
# VISTAS PARA USUARIOS REGISTRADOS
# ========================================

@usuario_autenticado
def pagina2(request):
    """
    Formulario de denuncia - SOLO usuarios registrados
    Cualquier usuario autenticado puede crear denuncias
    """
    categorias = Categoria.objects.all()

    if not categorias.exists():
        messages.error(request, '⚠️ No hay categorías disponibles. Contacta al administrador.')
        return redirect('index')

    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        categoria_id = request.POST.get('categoria')
        descripcion = request.POST.get('descripcion')
        ubicacion_texto = request.POST.get('ubicacion_texto')
        latitud = request.POST.get('latitud')
        longitud = request.POST.get('longitud')
        evidencia_url = request.POST.get('evidencia_url')
        prioridad = request.POST.get('prioridad', 'media')
        evidencia_file = request.FILES.get('evidencia')

        # Validar categoría
        if not categoria_id:
            messages.error(request, '⚠️ Debes seleccionar una categoría.')
            return render(request, 'pagina2.html', {'categorias': categorias})

        # Crear ubicación si hay coordenadas
        ubicacion = None
        if latitud and longitud:
            try:
                ubicacion = Ubicacion.objects.create(
                    latitud=latitud,
                    longitud=longitud,
                    descripcion=ubicacion_texto
                )
            except Exception as e:
                messages.error(request, f'⚠️ Error al guardar ubicación: {str(e)}')
                return render(request, 'pagina2.html', {'categorias': categorias})

        # Crear denuncia
        try:
            denuncia = Denuncia.objects.create(
                usuario=request.user,
                categoria_id=categoria_id,
                ubicacion=ubicacion,
                titulo=titulo,
                descripcion=descripcion,
                evidencia=evidencia_file,
                evidencia_url=evidencia_url if evidencia_url else None,
                estado='pendiente',
                prioridad=prioridad
            )

            # Registrar en historial
            HistorialDenuncia.objects.create(
                denuncia=denuncia,
                usuario=request.user,
                tipo_accion='creacion',
                cambio_descripcion=f'Denuncia creada: {titulo}'
            )

            # Registrar en log de actividad
            LogActividad.objects.create(
                usuario=request.user,
                accion=f'Creó denuncia: {titulo}',
                ip_origen=request.META.get('REMOTE_ADDR')
            )

            messages.success(request, '✅ ¡Denuncia enviada exitosamente!')
            return redirect('mis_denuncias')

        except Exception as e:
            messages.error(request, f'❌ Error al crear denuncia: {str(e)}')
            return render(request, 'pagina2.html', {'categorias': categorias})

    return render(request, 'pagina2.html', {'categorias': categorias})

@usuario_autenticado
def mis_denuncias(request):
    """
    Ver SOLO las denuncias propias del usuario
    Cada usuario ve únicamente sus propias denuncias
    """
    denuncias = Denuncia.objects.filter(usuario=request.user).select_related('categoria', 'ubicacion').order_by('-fecha_creacion')

    context = {
        'denuncias': denuncias,
        'total': denuncias.count(),
        'pendientes': denuncias.filter(estado='pendiente').count(),
        'resueltas': denuncias.filter(estado='resuelta').count(),
    }

    return render(request, 'mis_denuncias.html', context)

@usuario_autenticado
def editar_mi_denuncia(request, denuncia_id):
    """
    Editar SOLO denuncia propia (si está pendiente)
    Los usuarios solo pueden editar sus denuncias pendientes
    """
    denuncia = get_object_or_404(Denuncia, id=denuncia_id, usuario=request.user)

    # Solo se puede editar si está pendiente
    if denuncia.estado != 'pendiente':
        messages.error(request, '⚠️ No puedes editar una denuncia que ya fue procesada.')
        return redirect('mis_denuncias')

    categorias = Categoria.objects.all()

    if request.method == 'POST':
        denuncia.titulo = request.POST.get('titulo')
        denuncia.descripcion = request.POST.get('descripcion')
        categoria_id = request.POST.get('categoria')

        if categoria_id:
            denuncia.categoria_id = categoria_id

        # Actualizar archivo si se sube uno nuevo
        evidencia_file = request.FILES.get('evidencia')
        if evidencia_file:
            denuncia.evidencia = evidencia_file

        evidencia_url = request.POST.get('evidencia_url')
        if evidencia_url:
            denuncia.evidencia_url = evidencia_url

        denuncia.save()

        # Registrar en historial
        HistorialDenuncia.objects.create(
            denuncia=denuncia,
            usuario=request.user,
            tipo_accion='edicion',
            cambio_descripcion='Usuario editó su denuncia'
        )

        messages.success(request, '✅ Denuncia actualizada.')
        return redirect('mis_denuncias')

    return render(request, 'editar_mi_denuncia.html', {
        'denuncia': denuncia,
        'categorias': categorias
    })

@usuario_autenticado
def eliminar_mi_denuncia(request, denuncia_id):
    """
    Eliminar SOLO denuncia propia (si está pendiente)
    """
    denuncia = get_object_or_404(Denuncia, id=denuncia_id, usuario=request.user)

    if denuncia.estado != 'pendiente':
        messages.error(request, '⚠️ No puedes eliminar una denuncia que ya fue procesada.')
        return redirect('mis_denuncias')

    if request.method == 'POST':
        titulo = denuncia.titulo
        denuncia.delete()

        LogActividad.objects.create(
            usuario=request.user,
            accion=f'Eliminó su denuncia: {titulo}',
            ip_origen=request.META.get('REMOTE_ADDR')
        )

        messages.success(request, '✅ Denuncia eliminada.')
        return redirect('mis_denuncias')

    return render(request, 'confirmar_eliminar_denuncia.html', {'denuncia': denuncia})

# ========================================
# VISTAS PARA REVISOR Y ADMIN
# ========================================

@admin_o_revisor
def pagina6(request):
    """
    Gestión de TODAS las denuncias - SOLO revisor y admin
    Permite ver, filtrar y gestionar todas las denuncias del sistema
    """
    denuncias = Denuncia.objects.all().select_related('usuario', 'categoria', 'ubicacion').order_by('-fecha_creacion')

    # Filtros
    estado_filtro = request.GET.get('estado')
    prioridad_filtro = request.GET.get('prioridad')
    categoria_filtro = request.GET.get('categoria')
    busqueda = request.GET.get('q')

    if estado_filtro:
        denuncias = denuncias.filter(estado=estado_filtro)
    if prioridad_filtro:
        denuncias = denuncias.filter(prioridad=prioridad_filtro)
    if categoria_filtro:
        denuncias = denuncias.filter(categoria_id=categoria_filtro)
    if busqueda:
        denuncias = denuncias.filter(titulo__icontains=busqueda) | denuncias.filter(descripcion__icontains=busqueda)

    categorias = Categoria.objects.all()

    # Estadísticas rápidas
    total = Denuncia.objects.count()
    pendientes = Denuncia.objects.filter(estado='pendiente').count()
    en_proceso = Denuncia.objects.filter(estado='en_proceso').count()
    resueltas = Denuncia.objects.filter(estado='resuelta').count()

    context = {
        'denuncias': denuncias,
        'categorias': categorias,
        'estados': Denuncia.ESTADOS,
        'prioridades': Denuncia.PRIORIDADES,
        'total': total,
        'pendientes': pendientes,
        'en_proceso': en_proceso,
        'resueltas': resueltas,
    }

    return render(request, 'pagina6.html', context)

@admin_o_revisor
def editar_denuncia(request, denuncia_id):
    """
    Editar cualquier denuncia - SOLO revisor y admin
    Permite modificar título, descripción, estado y prioridad
    """
    denuncia = get_object_or_404(Denuncia, id=denuncia_id)
    categorias = Categoria.objects.all()

    if request.method == 'POST':
        estado_anterior = denuncia.estado
        prioridad_anterior = denuncia.prioridad

        denuncia.titulo = request.POST.get('titulo')
        denuncia.descripcion = request.POST.get('descripcion')
        denuncia.estado = request.POST.get('estado')
        denuncia.prioridad = request.POST.get('prioridad')

        categoria_id = request.POST.get('categoria')
        if categoria_id:
            denuncia.categoria_id = categoria_id

        denuncia.save()

        # Registrar cambios en historial
        cambios = []
        if estado_anterior != denuncia.estado:
            cambios.append(f'Estado: {estado_anterior} → {denuncia.estado}')
        if prioridad_anterior != denuncia.prioridad:
            cambios.append(f'Prioridad: {prioridad_anterior} → {denuncia.prioridad}')

        if cambios:
            HistorialDenuncia.objects.create(
                denuncia=denuncia,
                usuario=request.user,
                tipo_accion='edicion',
                cambio_descripcion=', '.join(cambios)
            )

        # Registrar en log
        LogActividad.objects.create(
            usuario=request.user,
            accion=f'Editó denuncia #{denuncia.id}: {denuncia.titulo}',
            ip_origen=request.META.get('REMOTE_ADDR')
        )

        messages.success(request, '✅ Denuncia actualizada.')
        return	redirect('pagina6')

    return render(request, 'editar_denuncia.html', {
        'denuncia': denuncia,
        'categorias': categorias
    })

@admin_o_revisor
def cambiar_estado_denuncia(request, denuncia_id):
    """
    Cambiar solo el estado de una denuncia - AJAX
    Para cambios rápidos desde la lista
    """
    if request.method == 'POST':
        denuncia = get_object_or_404(Denuncia, id=denuncia_id)
        nuevo_estado = request.POST.get('estado')

        if nuevo_estado in dict(Denuncia.ESTADOS).keys():
            estado_anterior = denuncia.estado
            denuncia.estado = nuevo_estado
            denuncia.save()

            # Registrar en historial
            HistorialDenuncia.objects.create(
                denuncia=denuncia,
                usuario=request.user,
                tipo_accion='cambio_estado',
                cambio_descripcion=f'Estado: {estado_anterior} → {nuevo_estado}'
            )

            LogActividad.objects.create(
                usuario=request.user,
                accion=f'Cambió estado de denuncia #{denuncia.id} a {nuevo_estado}',
                ip_origen=request.META.get('REMOTE_ADDR')
            )

            messages.success(request, f'✅ Estado cambiado a {denuncia.get_estado_display()}')
        else:
            messages.error(request, '⚠️ Estado inválido')

    return redirect('pagina6')

@admin_o_revisor
def ver_historial_denuncia(request, denuncia_id):
    """
    Ver historial completo de cambios de una denuncia
    """
    denuncia = get_object_or_404(Denuncia, id=denuncia_id)
    historial = HistorialDenuncia.objects.filter(denuncia=denuncia).select_related('usuario').order_by('-fecha')

    return render(request, 'historial_denuncia.html', {
        'denuncia': denuncia,
        'historial': historial
    })

# ========================================
# VISTAS SOLO PARA ADMIN
# ========================================

@solo_admin
def gestionar_usuarios(request):
    """
    Gestionar usuarios - SOLO admin
    Ver, crear, editar y cambiar roles de usuarios
    """
    usuarios = Usuario.objects.annotate(
        denuncias_count=Count('denuncias')
    ).order_by('-date_joined')

    # Filtros
    rol_filtro = request.GET.get('rol')
    busqueda = request.GET.get('q')

    if rol_filtro:
        usuarios = usuarios.filter(rol=rol_filtro)
    if busqueda:
        usuarios = usuarios.filter(
            username__icontains=busqueda
        ) | usuarios.filter(
            email__icontains=busqueda
        )

    # Estadísticas
    total_usuarios = Usuario.objects.count()
    total_admins = Usuario.objects.filter(rol='admin').count()
    total_revisores = Usuario.objects.filter(rol='revisor').count()
    total_usuarios_comunes = Usuario.objects.filter(rol='usuario').count()

    context = {
        'usuarios': usuarios,
        'total_usuarios': total_usuarios,
        'total_admins': total_admins,
        'total_revisores': total_revisores,
        'total_usuarios_comunes': total_usuarios_comunes,
    }

    return render(request, 'gestionar_usuarios.html', context)

@solo_admin
def cambiar_rol_usuario(request, usuario_id):
    """
    Cambiar rol de un usuario - SOLO admin
    """
    if request.method == 'POST':
        usuario = get_object_or_404(Usuario, id=usuario_id)
        nuevo_rol = request.POST.get('rol')

        if nuevo_rol in dict(Usuario.ROLES).keys():
            rol_anterior = usuario.get_rol_display()
            usuario.rol = nuevo_rol
            usuario.save()

            # Registrar en log
            LogActividad.objects.create(
                usuario=request.user,
                accion=f'Cambió rol de {usuario.username} de {rol_anterior} a {usuario.get_rol_display()}',
                ip_origen=request.META.get('REMOTE_ADDR')
            )

            messages.success(request, f'✅ Rol de {usuario.username} cambiado a {usuario.get_rol_display()}')
        else:
            messages.error(request, '⚠️ Rol inválido')

    return redirect('gestionar_usuarios')

@solo_admin
def activar_desactivar_usuario(request, usuario_id):
    """
    Activar o desactivar cuenta de usuario - SOLO admin
    """
    if request.method == 'POST':
        usuario = get_object_or_404(Usuario, id=usuario_id)

        # No permitir desactivarse a sí mismo
        if usuario == request.user:
            messages.error(request, '⚠️ No puedes desactivar tu propia cuenta.')
            return redirect('gestionar_usuarios')

        usuario.activo = not usuario.activo
        usuario.save()

        accion = 'activó' if usuario.activo else 'desactivó'
        LogActividad.objects.create(
            usuario=request.user,
            accion=f'{accion.capitalize()} cuenta de {usuario.username}',
            ip_origen=request.META.get('REMOTE_ADDR')
        )

        messages.success(request, f'✅ Cuenta de {usuario.username} {accion}.')

    return redirect('gestionar_usuarios')

@solo_admin
def ver_logs(request):
    """
    Ver logs de actividad - SOLO admin
    Registro de todas las acciones importantes del sistema
    """
    logs = LogActividad.objects.select_related('usuario').order_by('-fecha')[:200]

    # Filtros
    usuario_filtro = request.GET.get('usuario')
    fecha_filtro = request.GET.get('fecha')

    if usuario_filtro:
        logs = logs.filter(usuario_id=usuario_filtro)
    if fecha_filtro:
        logs = logs.filter(fecha__date=fecha_filtro)

    usuarios = Usuario.objects.all()

    return render(request, 'ver_logs.html', {
        'logs': logs,
        'usuarios': usuarios
    })

@solo_admin
def estadisticas_admin(request):
    """
    Estadísticas y reportes - SOLO admin
    Dashboard con métricas del sistema
    """
    # Estadísticas de denuncias
    total_denuncias = Denuncia.objects.count()
    pendientes = Denuncia.objects.filter(estado='pendiente').count()
    en_proceso = Denuncia.objects.filter(estado='en_proceso').count()
    resueltas = Denuncia.objects.filter(estado='resuelta').count()
    rechazadas = Denuncia.objects.filter(estado='rechazada').count()

    # Calcular porcentajes
    if total_denuncias > 0:
        porcentaje_pendientes = round((pendientes / total_denuncias) * 100, 1)
        porcentaje_proceso = round((en_proceso / total_denuncias) * 100, 1)
        porcentaje_resueltas = round((resueltas / total_denuncias) * 100, 1)
    else:
        porcentaje_pendientes = porcentaje_proceso = porcentaje_resueltas = 0

    # Denuncias por prioridad
    prioridad_alta = Denuncia.objects.filter(prioridad='alta').count()
    prioridad_media = Denuncia.objects.filter(prioridad='media').count()
    prioridad_baja = Denuncia.objects.filter(prioridad='baja').count()

    # Estadísticas de usuarios
    total_usuarios = Usuario.objects.count()
    usuarios_comunes = Usuario.objects.filter(rol='usuario').count()
    usuarios_revisores = Usuario.objects.filter(rol='revisor').count()
    usuarios_admins = Usuario.objects.filter(rol='admin').count()

    # Categorías
    total_categorias = Categoria.objects.count()

    # Top categorías con denuncias
    top_categorias_query = Categoria.objects.annotate(
        total=Count('denuncias')
    ).filter(total__gt=0).order_by('-total')[:5]

    # Preparar datos de categorías para el template
    categorias_list = []
    for cat in top_categorias_query:
        categorias_list.append({
            'nombre': cat.nombre,
            'total': cat.total
        })

    # Top usuarios más activos
    top_usuarios = Usuario.objects.annotate(
        denuncias_count=Count('denuncias')
    ).filter(denuncias_count__gt=0).order_by('-denuncias_count')[:5]

    # Denuncias recientes
    denuncias_recientes = Denuncia.objects.select_related(
        'usuario', 'categoria'
    ).order_by('-fecha_creacion')[:10]

    context = {
        'stats': {
            'total_denuncias': total_denuncias,
            'pendientes': pendientes,
            'en_proceso': en_proceso,
            'resueltas': resueltas,
            'rechazadas': rechazadas,
            'porcentaje_pendientes': porcentaje_pendientes,
            'porcentaje_proceso': porcentaje_proceso,
            'porcentaje_resueltas': porcentaje_resueltas,
            'prioridad_alta': prioridad_alta,
            'prioridad_media': prioridad_media,
            'prioridad_baja': prioridad_baja,
            'total_usuarios': total_usuarios,
            'usuarios_comunes': usuarios_comunes,
            'usuarios_revisores': usuarios_revisores,
            'usuarios_admins': usuarios_admins,
            'total_categorias': total_categorias,
        },
        'top_categorias': categorias_list,
        'top_usuarios': top_usuarios,
        'denuncias_recientes': denuncias_recientes,
    }

    return render(request, 'estadisticas_admin.html', context)

# ========================================
# VISTAS DE AUTENTICACIÓN (públicas)
# ========================================

def login_view(request):
    """Vista de login - Acceso público"""
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            if not user.activo:
                messages.error(request, '❌ Tu cuenta ha sido desactivada. Contacta al administrador.')
                return render(request, 'login.html')

            login(request, user)

            # Registrar login en logs
            LogActividad.objects.create(
                usuario=user,
                accion='Inicio de sesión',
                ip_origen=request.META.get('REMOTE_ADDR')
            )

            messages.success(request, f'✅ ¡Bienvenido, {user.username}!')

            # Redirigir según rol
            if user.es_admin() or user.es_revisor():
                return redirect('pagina6')
            else:
                return redirect('index')
        else:
            messages.error(request, '❌ Usuario o contraseña incorrectos.')

    return render(request, 'login.html')

def logout_view(request):
    """Vista de logout"""
    username = request.user.username if request.user.is_authenticated else None

    # Registrar logout
    if request.user.is_authenticated:
        LogActividad.objects.create(
            usuario=request.user,
            accion='Cierre de sesión',
            ip_origen=request.META.get('REMOTE_ADDR')
        )

    logout(request)

    if username:
        messages.success(request, f'👋 Sesión cerrada. Hasta pronto, {username}.')

    return redirect('index')

def registro_publico(request):
    """Registro de nuevos usuarios - Acceso público"""
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        telefono = request.POST.get('telefono', '')

        # Validaciones
        if password != password_confirm:
            messages.error(request, '❌ Las contraseñas no coinciden.')
            return render(request, 'registro_publico.html')

        if len(password) < 6:
            messages.error(request, '❌ La contraseña debe tener al menos 6 caracteres.')
            return render(request, 'registro_publico.html')

        if Usuario.objects.filter(username=username).exists():
            messages.error(request, '❌ El nombre de usuario ya está en uso.')
            return render(request, 'registro_publico.html')

        if Usuario.objects.filter(email=email).exists():
            messages.error(request, '❌ El correo ya está registrado.')
            return render(request, 'registro_publico.html')

        # Crear usuario (siempre rol 'usuario' por defecto)
        try:
            user = Usuario.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                telefono=telefono,
                rol='usuario',
                activo=True
            )

            # Registrar en logs
            LogActividad.objects.create(
                usuario=user,
                accion='Registro de nueva cuenta',
                ip_origen=request.META.get('REMOTE_ADDR')
            )

            messages.success(request, '✅ ¡Cuenta creada exitosamente! Ya puedes iniciar sesión.')
            return redirect('login_view')

        except Exception as e:
            messages.error(request, f'❌ Error al crear cuenta: {str(e)}')
            return render(request, 'registro_publico.html')

    return render(request, 'registro_publico.html')

@usuario_autenticado
def perfil_view(request):
    """Vista de perfil del usuario"""

    # Estadísticas del usuario
    mis_denuncias_total = Denuncia.objects.filter(usuario=request.user).count()
    mis_denuncias_pendientes = Denuncia.objects.filter(usuario=request.user, estado='pendiente').count()
    mis_denuncias_resueltas = Denuncia.objects.filter(usuario=request.user, estado='resuelta').count()

    context = {
        'usuario': request.user,
        'mis_denuncias_total': mis_denuncias_total,
        'mis_denuncias_pendientes': mis_denuncias_pendientes,
        'mis_denuncias_resueltas': mis_denuncias_resueltas,
    }

    return render(request, 'perfil.html', context)

# ========================================
# API REST (JSON)
# ========================================

def lista_denuncias(request):
    """Lista de denuncias en formato JSON - Acceso público"""
    denuncias = Denuncia.objects.all().select_related('usuario', 'categoria')
    datos = []

    for denuncia in denuncias:
        datos.append({
            'id': denuncia.id,
            'titulo': denuncia.titulo,
            'categoria': denuncia.categoria.nombre if denuncia.categoria else 'Sin categoría',
            'descripcion': denuncia.descripcion[:100] + '...' if len(denuncia.descripcion) > 100 else denuncia.descripcion,
            'estado': denuncia.get_estado_display(),
            'prioridad': denuncia.get_prioridad_display(),
            'usuario': denuncia.usuario.username,
            'fecha_creacion': denuncia.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S')
        })

    return JsonResponse(datos, safe=False)

@api_view(['GET'])
def estadisticas_denuncias(request):
    """Estadísticas de denuncias - API REST"""

    total = Denuncia.objects.count()
    pendientes = Denuncia.objects.filter(estado='pendiente').count()
    en_proceso = Denuncia.objects.filter(estado='en_proceso').count()
    resueltas = Denuncia.objects.filter(estado='resuelta').count()
    rechazadas = Denuncia.objects.filter(estado='rechazada').count()

    baja = Denuncia.objects.filter(prioridad='baja').count()
    media = Denuncia.objects.filter(prioridad='media').count()
    alta = Denuncia.objects.filter(prioridad='alta').count()

    return Response({
        'total_denuncias': total,
        'por_estado': {
            'pendientes': pendientes,
            'en_proceso': en_proceso,
            'resueltas': resueltas,
            'rechazadas': rechazadas
        },
        'por_prioridad': {
            'baja': baja,
            'media': media,
            'alta': alta
        }
    })

@api_view(['GET'])
def denuncias_recientes(request):
    """Últimas 5 denuncias - API REST"""
    denuncias = Denuncia.objects.all().select_related('usuario', 'categoria').order_by('-fecha_creacion')[:5]

    datos = []
    for denuncia in denuncias:
        datos.append({
            'id': denuncia.id,
            'titulo': denuncia.titulo,
            'descripcion': denuncia.descripcion[:100] + '...' if len(denuncia.descripcion) > 100 else denuncia.descripcion,
            'categoria': denuncia.categoria.nombre if denuncia.categoria else 'Sin categoría',
            'estado': denuncia.get_estado_display(),
            'prioridad': denuncia.get_prioridad_display(),
            'fecha_creacion': denuncia.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S'),
            'usuario': denuncia.usuario.username
        })

    return Response(datos)

@usuario_autenticado
def pagina7(request):
    return redirect('pagina2')

# ========================================
# PÁGINA 3: FLORA Y FAUNA POR UBICACIÓN
# ========================================
def pagina3(request):
    """
    Flora y Fauna por ubicación usando iNaturalist (Chile) a partir de observaciones con foto.
    - Siempre filtra por Chile.
    - Además filtra por el texto que escribas (q), ej: 'camote', 'cóndor', 'puma'.
    """
    ubicacion = request.GET.get('ubicacion', '').strip()
    page = int(request.GET.get('page', 1))
    items_per_page = 30

    flora_results = []
    fauna_results = []
    error_message = None

    # Si no hay texto, no buscamos nada (para no traer 9 millones de resultados)
    if ubicacion:
        try:
            place_id_chile = 6793  # Chile

            url = "https://api.inaturalist.org/v1/observations"
            params = {
                "place_id": place_id_chile,
                "per_page": items_per_page,
                "page": page,
                "order_by": "created_at",
                "order": "desc",
                "locale": "es",
                "preferred_place_id": place_id_chile,
                "verifiable": "true",
                "photos": "true",
                "q": ubicacion,  # <- texto que escribes (nombre común / científico) [web:192]
            }

            r = requests.get(url, params=params, timeout=10)
            if r.status_code == 200:
                data = r.json()
                results = data.get("results", [])

                for obs in results:
                    taxon = obs.get("taxon") or {}
                    if not taxon:
                        continue

                    # nombre común en español si existe
                    common_name = taxon.get("preferred_common_name")
                    if not common_name:
                        for n in taxon.get("names", []):
                            if n.get("lexicon") == "Spanish":
                                common_name = n.get("name")
                                break

                    scientific_name = taxon.get("name") or ""

                    # FOTO: usar primera foto de la observación
                    default_photo = None
                    photos = obs.get("photos") or []
                    if photos:
                        default_photo = (
                            photos[0].get("url")
                            or photos[0].get("medium_url")
                            or photos[0].get("square_url")
                        )

                    iconic = (taxon.get("iconic_taxon_name") or "").lower()

                    item = {
                        "nombre_comun": common_name or "Sin nombre común",
                        "nombre_cientifico": scientific_name,
                        "descripcion": "",
                        "imagen": default_photo,
                        "tipo": iconic.capitalize(),
                        "ciclo": "",
                        "nombre": common_name or scientific_name,
                        "habitat": "",
                        "dieta": "",
                        "poblacion": "",
                        "ubicaciones": "Chile",
                    }

                    if iconic == "plantae":
                        flora_results.append(item)
                    elif iconic in [
                        "animalia", "aves", "mammalia", "reptilia",
                        "amphibia", "actinopterygii", "arachnida", "insecta"
                    ]:
                        fauna_results.append(item)
            else:
                error_message = "No se pudo obtener información desde iNaturalist por ahora."
        except Exception as e:
            print("DEBUG INAT ERROR:", repr(e))
            error_message = "Error al conectar con el servicio de biodiversidad."

    context = {
        "ubicacion": ubicacion,
        "page": page,
        "flora_results": flora_results,
        "fauna_results": fauna_results,
        "error_message": error_message,
        "hay_mas_flora": len(flora_results) == items_per_page,
        "hay_mas_fauna": len(fauna_results) == items_per_page,
    }
    return render(request, "pagina3.html", context)
