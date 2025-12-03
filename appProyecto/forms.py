from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
import re
from .models import Denuncia, Usuario, Categoria, Ubicacion


# ==============================================================================
# FORMULARIO DE DENUNCIA (ADMIN/REVISOR)
# ==============================================================================

class DenunciaForm(forms.ModelForm):
    """
    Formulario completo de denuncia con ubicación GPS
    Usado por admin/revisor para gestionar denuncias
    """
    latitud = forms.DecimalField(
        required=False,
        max_digits=9,
        decimal_places=6,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Latitud GPS (opcional)',
            'step': 'any'
        })
    )
    longitud = forms.DecimalField(
        required=False,
        max_digits=11,
        decimal_places=8,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Longitud GPS (opcional)',
            'step': 'any'
        })
    )
    ubicacion_texto = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Parque Nacional, Calle Principal, etc.'
        }),
        label='Ubicación'
    )
    
    class Meta:
        model = Denuncia
        fields = [
            'usuario',
            'categoria',
            'titulo',
            'descripcion',
            'evidencia',
            'evidencia_url',
            'estado',
            'prioridad'
        ]
        widgets = {
            'usuario': forms.Select(attrs={
                'class': 'form-control'
            }),
            'categoria': forms.Select(attrs={
                'class': 'form-control'
            }),
            'titulo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título breve del problema',
                'maxlength': '200'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Describe detalladamente el problema ambiental',
                'rows': 5
            }),
            'evidencia': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*,video/*,.pdf'
            }),
            'evidencia_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://ejemplo.com/imagen.jpg (opcional)'
            }),
            'estado': forms.Select(attrs={
                'class': 'form-control'
            }),
            'prioridad': forms.Select(attrs={
                'class': 'form-control'
            })
        }
        labels = {
            'titulo': 'Título de la Denuncia',
            'descripcion': 'Descripción Detallada',
            'evidencia': 'Evidencia (archivo)',
            'evidencia_url': 'Evidencia (URL)',
            'estado': 'Estado',
            'prioridad': 'Nivel de Prioridad',
            'usuario': 'Usuario',
            'categoria': 'Categoría'
        }
    
    def clean_titulo(self):
        """Validar longitud del título"""
        titulo = self.cleaned_data.get('titulo')
        if len(titulo) < 10:
            raise ValidationError('El título debe tener al menos 10 caracteres.')
        if len(titulo) > 200:
            raise ValidationError('El título no puede exceder los 200 caracteres.')
        return titulo
    
    def clean_descripcion(self):
        """Validar longitud de descripción"""
        descripcion = self.cleaned_data.get('descripcion')
        if len(descripcion) < 20:
            raise ValidationError('La descripción debe tener al menos 20 caracteres.')
        if len(descripcion) > 2000:
            raise ValidationError('La descripción no puede exceder los 2000 caracteres.')
        return descripcion
    
    def clean_evidencia(self):
        """Validar archivo de evidencia"""
        evidencia = self.cleaned_data.get('evidencia')
        if evidencia:
            # Validar tamaño (10MB máximo)
            if evidencia.size > 10 * 1024 * 1024:
                raise ValidationError('El archivo no debe superar los 10MB.')
            
            # Validar extensión
            extensiones_permitidas = ['jpg', 'jpeg', 'png', 'gif', 'pdf', 'mp4', 'mov']
            extension = evidencia.name.lower().split('.')[-1]
            if extension not in extensiones_permitidas:
                raise ValidationError(f'Formato no permitido. Usa: {", ".join(extensiones_permitidas)}')
        
        return evidencia
    
    def clean_ubicacion_texto(self):
        """Validar ubicación texto"""
        ubicacion = self.cleaned_data.get('ubicacion_texto')
        if len(ubicacion) < 5:
            raise ValidationError('La ubicación debe tener al menos 5 caracteres.')
        return ubicacion
    
    def save(self, commit=True):
        """Guardar denuncia con ubicación"""
        denuncia = super().save(commit=False)
        
        latitud = self.cleaned_data.get('latitud')
        longitud = self.cleaned_data.get('longitud')
        ubicacion_texto = self.cleaned_data.get('ubicacion_texto')
        
        if latitud and longitud:
            ubicacion, created = Ubicacion.objects.get_or_create(
                latitud=latitud,
                longitud=longitud,
                defaults={'descripcion': ubicacion_texto}
            )
            denuncia.ubicacion = ubicacion
        
        if commit:
            denuncia.save()
        
        return denuncia


# ==============================================================================
# FORMULARIO DE DENUNCIA PÚBLICA (USUARIOS)
# ==============================================================================

class DenunciaPublicaForm(forms.ModelForm):
    """
    Formulario simplificado para usuarios regulares
    No incluye estado ni prioridad (se asignan automáticamente)
    """
    ubicacion_texto = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Parque Nacional Torres del Paine'
        }),
        label='Ubicación del incidente'
    )
    
    latitud = forms.DecimalField(
        required=False,
        max_digits=9,
        decimal_places=6,
        widget=forms.HiddenInput()
    )
    
    longitud = forms.DecimalField(
        required=False,
        max_digits=11,
        decimal_places=8,
        widget=forms.HiddenInput()
    )
    
    class Meta:
        model = Denuncia
        fields = ['categoria', 'titulo', 'descripcion', 'evidencia', 'evidencia_url']
        widgets = {
            'categoria': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'titulo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título breve del problema',
                'maxlength': '200'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Describe el problema ambiental que observaste',
                'rows': 5
            }),
            'evidencia': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*,video/*,.pdf'
            }),
            'evidencia_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://ejemplo.com/imagen.jpg (opcional)'
            })
        }
        labels = {
            'categoria': 'Categoría',
            'titulo': 'Título',
            'descripcion': 'Descripción',
            'evidencia': 'Evidencia (archivo)',
            'evidencia_url': 'Evidencia (URL - opcional)'
        }
    
    def clean_titulo(self):
        """Validar título"""
        titulo = self.cleaned_data.get('titulo')
        if len(titulo) < 10:
            raise ValidationError('El título debe tener al menos 10 caracteres.')
        return titulo
    
    def clean_descripcion(self):
        """Validar descripción"""
        descripcion = self.cleaned_data.get('descripcion')
        if len(descripcion) < 20:
            raise ValidationError('La descripción debe tener al menos 20 caracteres.')
        return descripcion
    
    def clean_evidencia(self):
        """Validar archivo"""
        evidencia = self.cleaned_data.get('evidencia')
        if evidencia:
            if evidencia.size > 10 * 1024 * 1024:
                raise ValidationError('El archivo no debe superar los 10MB.')
        return evidencia


# ==============================================================================
# FORMULARIO DE REGISTRO DE USUARIOS
# ==============================================================================

class RegistroForm(forms.ModelForm):
    """
    Formulario de registro con validaciones de seguridad
    """
    password = forms.CharField(
        min_length=8,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Mínimo 8 caracteres'
        }),
        label='Contraseña',
        help_text='Debe contener al menos 8 caracteres, letras y números'
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirma tu contraseña'
        }),
        label='Confirmar Contraseña'
    )
    
    class Meta:
        model = Usuario
        fields = ['username', 'email', 'first_name', 'last_name', 'telefono']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Usuario único (mín. 4 caracteres)'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'correo@ejemplo.com'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Apellido'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+56912345678 (opcional)'
            })
        }
        labels = {
            'username': 'Nombre de Usuario',
            'email': 'Correo Electrónico',
            'first_name': 'Nombre',
            'last_name': 'Apellido',
            'telefono': 'Teléfono'
        }
    
    def clean_username(self):
        """Validar username único y formato"""
        username = self.cleaned_data.get('username')
        
        # Validar que no exista
        if Usuario.objects.filter(username=username).exists():
            raise ValidationError('Este nombre de usuario ya está en uso.')
        
        # Validar formato (solo letras, números y guiones bajos)
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            raise ValidationError('Solo se permiten letras, números y guiones bajos.')
        
        # Validar longitud mínima
        if len(username) < 4:
            raise ValidationError('El usuario debe tener al menos 4 caracteres.')
        
        return username
    
    def clean_email(self):
        """Validar email único"""
        email = self.cleaned_data.get('email')
        
        if Usuario.objects.filter(email=email).exists():
            raise ValidationError('Este correo electrónico ya está registrado.')
        
        return email
    
    def clean_telefono(self):
        """Validar formato de teléfono chileno"""
        telefono = self.cleaned_data.get('telefono')
        
        if telefono:
            telefono_limpio = telefono.replace(' ', '').replace('-', '')
            
            # Validar formato chileno
            if not re.match(r'^(\+56)?[9]\d{8}$', telefono_limpio):
                raise ValidationError('Formato inválido. Usa: +56912345678 o 912345678')
            
            return telefono_limpio
        
        return telefono
    
    def clean(self):
        """Validar contraseñas y complejidad"""
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password and password_confirm:
            if password != password_confirm:
                raise ValidationError('Las contraseñas no coinciden.')
            
            # Validar complejidad
            if not re.search(r'[A-Za-z]', password):
                raise ValidationError('La contraseña debe contener al menos una letra.')
            
            if not re.search(r'\d', password):
                raise ValidationError('La contraseña debe contener al menos un número.')
        
        return cleaned_data


# ==============================================================================
# FORMULARIO DE LOGIN
# ==============================================================================

class LoginForm(forms.Form):
    """
    Formulario de inicio de sesión
    """
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Usuario',
            'autofocus': True
        }),
        label='Usuario'
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Contraseña'
        }),
        label='Contraseña'
    )
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Recordarme (7 días)'
    )


# ==============================================================================
# FORMULARIOS ADICIONALES
# ==============================================================================

class CambiarRolForm(forms.ModelForm):
    """Formulario para cambiar rol (solo admin)"""
    class Meta:
        model = Usuario
        fields = ['rol']
        widgets = {
            'rol': forms.Select(attrs={'class': 'form-control'})
        }


class EditarDenunciaAdminForm(forms.ModelForm):
    """Formulario para editar estado/prioridad (admin/revisor)"""
    class Meta:
        model = Denuncia
        fields = ['categoria', 'titulo', 'descripcion', 'estado', 'prioridad']
        widgets = {
            'categoria': forms.Select(attrs={'class': 'form-control'}),
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'estado': forms.Select(attrs={'class': 'form-control'}),
            'prioridad': forms.Select(attrs={'class': 'form-control'}),
        }
