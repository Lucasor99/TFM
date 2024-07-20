from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.views import LoginView
from django.contrib.auth.forms import AuthenticationForm
from .forms import UserRegisterForm
from django.shortcuts import redirect
from django.contrib.auth.models import User
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import user_passes_test

def redirect_to_login(request):
    return redirect('login')

def register(request):
    message = None
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # Establecer is_active en False
            user.save()
            message = 'Tu cuenta ha sido creada pero aún no está activa. Por favor, espera a que el administrador active tu cuenta.'
            form = UserRegisterForm() 
    else:
        form = UserRegisterForm()
    return render(request, 'register.html', {'form': form, 'message': message})

class CustomLoginView(LoginView):
    authentication_form = AuthenticationForm
    template_name = 'login.html'
    redirect_authenticated_user = True  # Redirigir usuarios autenticados

@user_passes_test(lambda u: u.is_superuser)
def manage_users(request):
    users = User.objects.all()

    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        action = request.POST.get('action')
        user = User.objects.get(id=user_id)

        if action == 'activate':
            user.is_active = True
            user.save()
        elif action == 'deactivate':
            user.is_active = False
            user.save()
        elif action == 'make_staff':
            user.is_staff = True
            user.save()
        elif action == 'remove_staff':
            user.is_staff = False
            user.save()

        return redirect('manage_users')  # Redirigir a la misma vista después de la acción

    return render(request, 'manage_users.html', {'users': users})

