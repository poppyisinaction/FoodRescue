from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from .forms import UserRegisterForm, UserUpdateForm, UserProfileUpdateForm
from notifications.models import Notification


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard_redirect')
        
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            
            # The post_save signal created the UserProfile; now populate profile fields
            profile = user.profile
            profile.role = form.cleaned_data['role']
            profile.phone = form.cleaned_data['phone']
            profile.organization_name = form.cleaned_data['organization_name']
            profile.organization_type = form.cleaned_data['organization_type']
            profile.city = form.cleaned_data['city']
            profile.address = form.cleaned_data['address']
            profile.verification_status = 'PENDING'
            profile.save()

            # Welcome notification
            Notification.objects.create(
                recipient=user,
                title="Welcome to FoodRescue!",
                message=f"Thank you for registering as a {profile.get_role_display()}. Your account is currently in verification review.",
                notification_type='SYSTEM',
                link='/accounts/profile/'
            )
            
            # Auto login
            login(request, user)
            messages.success(request, f"Welcome to FoodRescue, {user.first_name or user.username}! Your account has been registered successfully.")
            return redirect('dashboard_redirect')
        else:
            messages.error(request, "Please correct the errors below to complete your registration.")
    else:
        role_preselect = request.GET.get('role', 'DONOR')
        initial_data = {'role': role_preselect if role_preselect in ['DONOR', 'NGO'] else 'DONOR'}
        form = UserRegisterForm(initial=initial_data)
        
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard_redirect')
        
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {user.first_name or user.username}!")
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect('dashboard_redirect')
        else:
            messages.error(request, "Invalid username or password. Please try again.")
    else:
        form = AuthenticationForm()
        
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('home')


@login_required
def dashboard_redirect_view(request):
    if request.user.is_superuser or request.user.profile.is_platform_admin:
        return redirect('admin_dashboard')
    elif request.user.profile.is_donor:
        return redirect('donor_dashboard')
    elif request.user.profile.is_ngo:
        return redirect('ngo_dashboard')
    return redirect('home')


@login_required
def profile_view(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = UserProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, "Your profile details have been updated successfully.")
            return redirect('profile')
        else:
            messages.error(request, "Please check the form inputs for errors.")
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = UserProfileUpdateForm(instance=request.user.profile)
        
    context = {
        'u_form': u_form,
        'p_form': p_form,
        'profile': request.user.profile,
    }
    return render(request, 'accounts/profile.html', context)


def forgot_password_view(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        user_exists = User.objects.filter(email=email).exists()
        if user_exists:
            messages.success(request, "If an account matches that email address, a password reset link has been dispatched.")
        else:
            messages.info(request, "If an account matches that email address, a password reset link has been dispatched.")
        return redirect('login')
    return render(request, 'accounts/forgot_password.html')
