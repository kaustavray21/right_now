from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from .forms import SignUpForm
from .models import LoginHistory
from django.utils import timezone
import json
from datetime import datetime

def home(request):
    return render(request, 'home.html')

def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                LoginHistory.objects.create(user=user)
                return redirect('dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('home')

@login_required
def dashboard_view(request):
    selected_date_str = request.GET.get('date')
    if selected_date_str:
        try:
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = timezone.localdate()
    else:
        selected_date = timezone.localdate()

    login_history_for_day = LoginHistory.objects.filter(
        user=request.user,
        login_timestamp__date=selected_date
    ).order_by('-login_timestamp')

    total_logins_for_day = login_history_for_day.count()

    selected_date_formatted = selected_date.strftime('%B %d, %Y')

    all_user_logins = LoginHistory.objects.filter(user=request.user)
    total_logins = all_user_logins.count()

    time_of_day_counts = {
        "Morning": 0, "Afternoon": 0, "Evening": 0, "Night": 0,
    }
    for login_record in all_user_logins:
        local_time = timezone.localtime(login_record.login_timestamp)
        hour = local_time.hour
        if 5 <= hour < 12:
            time_of_day_counts["Morning"] += 1
        elif 12 <= hour < 17:
            time_of_day_counts["Afternoon"] += 1
        elif 17 <= hour < 21:
            time_of_day_counts["Evening"] += 1
        else:
            time_of_day_counts["Night"] += 1
    
    chart_labels = json.dumps(list(time_of_day_counts.keys()))
    chart_data = json.dumps(list(time_of_day_counts.values()))

    context = {
        'total_logins': total_logins,
        'login_history': login_history_for_day,
        'total_logins_today': total_logins_for_day,
        'selected_date_str': selected_date.strftime('%Y-%m-%d'),
        'selected_date_formatted': selected_date_formatted,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
    }
    return render(request, 'dashboard.html', context)

