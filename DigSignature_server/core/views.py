from django.shortcuts import render
from django.http import HttpResponse

def dashboard(request):
    """Vista principal del dashboard"""
    # TODO: Agregar datos reales cuando tengamos los modelos
    context = {
        'total_players': 12,
        'online_players': 8,
        'total_assets': 45,
        'total_playlists': 7,
    }
    return render(request, 'core/dashboard.html', context)

def settings_view(request):
    """Vista de configuración del sistema"""
    return HttpResponse("Settings - PiSignage")

def activity_log(request):
    """Vista del log de actividades"""
    return HttpResponse("Activity Log - PiSignage")

def dashboard_players_status(request):
    """API endpoint para HTMX - estado de players"""
    return render(request, 'partials/players_status_table.html')

def system_health(request):
    """API endpoint para HTMX - salud del sistema"""
    return HttpResponse("System Health API")