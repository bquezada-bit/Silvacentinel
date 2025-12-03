from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps


def rol_requerido(*roles_permitidos):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, '⚠️ Debes iniciar sesión para acceder a esta página.')
                return redirect('login_view')
            if request.user.rol not in roles_permitidos:
                messages.error(request, '🚫 No tienes permisos para acceder a esta página.')
                return redirect('index')
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def solo_admin(view_func):
    return rol_requerido('admin')(view_func)


def admin_o_revisor(view_func):
    return rol_requerido('admin', 'revisor')(view_func)


def usuario_autenticado(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, '⚠️ Debes iniciar sesión para acceder.')
            return redirect('login_view')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
