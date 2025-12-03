from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views


# ========================================
# ROUTER PARA REST FRAMEWORK API
# ========================================

router = DefaultRouter()

# Comentar ViewSets temporalmente hasta que los serializers estén listos
# router.register(r'denuncias', views.DenunciaViewSet, basename='api-denuncia')
# router.register(r'categorias', views.CategoriaViewSet, basename='api-categoria')
# router.register(r'observaciones', views.ObservacionViewSet, basename='api-observacion')


# ========================================
# URLS PRINCIPALES
# ========================================

urlpatterns = [
    # ========================================
    # PÁGINAS PÚBLICAS (sin autenticación)
    # ========================================
    path('', views.index, name='index'),
    path('inicio/', views.index, name='inicio'),
    path('quienes-somos/', views.pagina1, name='pagina1'),
    path('contactanos/', views.pagina4, name='pagina4'),
    path('tecnicas-ambientales/', views.pagina5, name='pagina5'),
    path('pagina3/', views.pagina3, name='pagina3'),
    
    # ========================================
    # AUTENTICACIÓN (páginas públicas)
    # ========================================
    path('login/', views.login_view, name='login_view'),
    path('logout/', views.logout_view, name='logout_view'),
    path('registro/', views.registro_publico, name='registro_publico'),
    
    # ========================================
    # USUARIOS REGISTRADOS (cualquier usuario autenticado)
    # ========================================
    path('crear-denuncia/', views.pagina2, name='pagina2'),
    path('nueva-denuncia/', views.pagina2, name='nueva_denuncia'),  
    path('mis-denuncias/', views.mis_denuncias, name='mis_denuncias'),
    path('editar-mi-denuncia/<int:denuncia_id>/', views.editar_mi_denuncia, name='editar_mi_denuncia'),
    path('eliminar-mi-denuncia/<int:denuncia_id>/', views.eliminar_mi_denuncia, name='eliminar_mi_denuncia'),
    path('perfil/', views.perfil_view, name='perfil_view'),
    path('mi-perfil/', views.perfil_view, name='mi_perfil'),  
    
    # ========================================
    # REVISOR Y ADMIN (gestión de denuncias)
    # ========================================
    path('gestion-denuncias/', views.pagina6, name='pagina6'),
    path('gestionar-denuncias/', views.pagina6, name='gestionar_denuncias'),  
    path('editar-denuncia/<int:denuncia_id>/', views.editar_denuncia, name='editar_denuncia'),
    path('cambiar-estado/<int:denuncia_id>/', views.cambiar_estado_denuncia, name='cambiar_estado_denuncia'),
    path('historial-denuncia/<int:denuncia_id>/', views.ver_historial_denuncia, name='ver_historial_denuncia'),
    
    # ========================================
    # SOLO ADMIN (gestión de usuarios y sistema)
    # ========================================
    path('gestionar-usuarios/', views.gestionar_usuarios, name='gestionar_usuarios'),
    path('admin/usuarios/', views.gestionar_usuarios, name='admin_usuarios'),  # Alias
    path('cambiar-rol/<int:usuario_id>/', views.cambiar_rol_usuario, name='cambiar_rol_usuario'),
    path('activar-desactivar/<int:usuario_id>/', views.activar_desactivar_usuario, name='activar_desactivar_usuario'),
    path('logs/', views.ver_logs, name='ver_logs'),
    path('admin/logs/', views.ver_logs, name='admin_logs'),  # Alias
    path('estadisticas/', views.estadisticas_admin, name='estadisticas_admin'),
    path('admin/estadisticas/', views.estadisticas_admin, name='admin_estadisticas'),  # Alias
    
    # ========================================
    # API JSON (acceso público/autenticado según endpoint)
    # ========================================
    path('api/denuncias/lista/', views.lista_denuncias, name='lista_denuncias'),
    path('api/denuncias/estadisticas/', views.estadisticas_denuncias, name='estadisticas_denuncias'),
    path('api/denuncias/recientes/', views.denuncias_recientes, name='denuncias_recientes'),
    
    # ========================================
    # REST FRAMEWORK ROUTER 
    # ========================================
    # path('api/', include(router.urls)),
    
    # ========================================
    # PÁGINAS ANTIGUAS 
    # ========================================
    path('pagina1/', views.pagina1, name='pagina1_legacy'),
    path('pagina2/', views.pagina2, name='pagina2_legacy'),
    path('pagina4/', views.pagina4, name='pagina4_legacy'),
    path('pagina5/', views.pagina5, name='pagina5_legacy'),
    path('pagina6/', views.pagina6, name='pagina6_legacy'),
    path('pagina7/', views.pagina7, name='pagina7'),
   
]
