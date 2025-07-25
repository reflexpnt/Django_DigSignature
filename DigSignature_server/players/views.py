from django.shortcuts import render
from django.http import HttpResponse

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.shortcuts import get_object_or_404, render
from .models import Player, DeviceLog, Group
import json
from datetime import datetime
from django.conf import settings as DjangoSETTINGs


def players_list(request):
    """Lista de players"""
    return HttpResponse("Players List - {DjangoSETTINGs.APP_NAME}")

def player_register(request):
    """Registro de nuevo player"""
    return HttpResponse("Player Registration - {DjangoSETTINGs.APP_NAME}")

def player_detail(request, pk):
    """Detalle de player específico"""
    return HttpResponse(f"Player Detail {pk} - {DjangoSETTINGs.APP_NAME}")

def player_edit(request, pk):
    """Editar player"""
    return HttpResponse(f"Edit Player {pk} - {DjangoSETTINGs.APP_NAME}")

def player_delete(request, pk):
    """Eliminar player"""
    return HttpResponse(f"Delete Player {pk} - {DjangoSETTINGs.APP_NAME}")

def player_sync(request, pk):
    """Sincronizar player"""
    return HttpResponse(f"Sync Player {pk} - {DjangoSETTINGs.APP_NAME}")

def player_screenshot(request, pk):
    """Screenshot de player"""
    return HttpResponse(f"Screenshot Player {pk} - {DjangoSETTINGs.APP_NAME}")

def groups_list(request):
    """Lista de grupos"""
    return HttpResponse("Groups List - {DjangoSETTINGs.APP_NAME}")

def group_create(request):
    """Crear grupo"""
    return HttpResponse("Create Group - {DjangoSETTINGs.APP_NAME}")

def group_detail(request, pk):
    """Detalle de grupo"""
    return HttpResponse(f"Group Detail {pk} - {DjangoSETTINGs.APP_NAME}")

def group_edit(request, pk):
    """Editar grupo"""
    return HttpResponse(f"Edit Group {pk} - {DjangoSETTINGs.APP_NAME}")

def group_delete(request, pk):
    """Eliminar grupo"""
    return HttpResponse(f"Delete Group {pk} - {DjangoSETTINGs.APP_NAME}")

def group_deploy(request, pk):
    """Desplegar a grupo"""
    return HttpResponse(f"Deploy to Group {pk} - {DjangoSETTINGs.APP_NAME}")



# players/views.py - Agregar estas vistas para la API

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.shortcuts import get_object_or_404, render
from .models import Player, DeviceLog
import json
from datetime import datetime

@csrf_exempt
@require_http_methods(["POST"])
def device_log_batch(request):
    
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        
        if not device_id:
            return JsonResponse({
                'status': 'error',
                'message': 'device_id is required'
            }, status=400)
        
        # Verificar que el device esté registrado
        try:
            player = Player.objects.get(device_id=device_id)
        except Player.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Device not registered'
            }, status=404)
        
        logs_data = data.get('logs', [])
        device_context = data.get('device_context', {})
        app_version = data.get('app_version', '')
        
        created_logs = []
        
        for log_entry in logs_data:
            try:
                # Parse device timestamp
                device_timestamp_str = log_entry.get('timestamp')
                if device_timestamp_str:
                    device_timestamp = datetime.fromisoformat(
                        device_timestamp_str.replace('Z', '+00:00')
                    )
                else:
                    device_timestamp = timezone.now()
                
                # Create log entry
                device_log = DeviceLog.objects.create(
                    player=player,
                    device_timestamp=device_timestamp,
                    level=log_entry.get('level', 'INFO'),
                    category=log_entry.get('category', 'APP'),
                    tag=log_entry.get('tag', 'Unknown'),
                    message=log_entry.get('message', ''),
                    thread_name=log_entry.get('thread_name', ''),
                    method_name=log_entry.get('method_name', ''),
                    line_number=log_entry.get('line_number'),
                    exception_class=log_entry.get('exception_class', ''),
                    stack_trace=log_entry.get('stack_trace', ''),
                    app_version=app_version,
                    battery_level=device_context.get('battery_level'),
                    memory_available_mb=device_context.get('memory_available_mb'),
                    extra_data=log_entry.get('extra_data', {})
                )
                
                created_logs.append(device_log.id)
                
            except Exception as e:
                # Log individual entry error but continue processing
                print(f"Error processing log entry: {e}")
                continue
        
        return JsonResponse({
            'status': 'success',
            'message': f'Processed {len(created_logs)} log entries',
            'created_logs': len(created_logs),
            'server_timestamp': timezone.now().isoformat()
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON'
        }, status=400)
    
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Server error: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def device_log_single(request):
    
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        
        if not device_id:
            return JsonResponse({
                'status': 'error',
                'message': 'device_id is required'
            }, status=400)
        
        try:
            player = Player.objects.get(device_id=device_id)
        except Player.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Device not registered'
            }, status=404)
        
        # Parse device timestamp
        device_timestamp_str = data.get('timestamp')
        if device_timestamp_str:
            device_timestamp = datetime.fromisoformat(
                device_timestamp_str.replace('Z', '+00:00')
            )
        else:
            device_timestamp = timezone.now()
        
        # Create log entry
        device_log = DeviceLog.objects.create(
            player=player,
            device_timestamp=device_timestamp,
            level=data.get('level', 'INFO'),
            category=data.get('category', 'APP'),
            tag=data.get('tag', 'Unknown'),
            message=data.get('message', ''),
            thread_name=data.get('thread_name', ''),
            method_name=data.get('method_name', ''),
            line_number=data.get('line_number'),
            exception_class=data.get('exception_class', ''),
            stack_trace=data.get('stack_trace', ''),
            app_version=data.get('app_version', ''),
            battery_level=data.get('battery_level'),
            memory_available_mb=data.get('memory_available_mb'),
            extra_data=data.get('extra_data', {})
        )
        
        return JsonResponse({
            'status': 'success',
            'message': 'Log entry created',
            'log_id': device_log.id,
            'server_timestamp': timezone.now().isoformat()
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON'
        }, status=400)
    
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Server error: {str(e)}'
        }, status=500)


def device_logs_terminal(request, device_id):
    """
    Vista template estilo terminal para mostrar logs de un dispositivo
    """
    player = get_object_or_404(Player, device_id=device_id)
    
    # Obtener parámetros de filtro
    level_filter = request.GET.get('level', '')
    category_filter = request.GET.get('category', '')
    hours = int(request.GET.get('hours', 24))
    search = request.GET.get('search', '')
    
    # Construir queryset
    #logs = player.get_recent_logs(hours=hours)
    logs = player.get_recent_logs(hours=hours).order_by('device_timestamp')
    
    if level_filter:
        logs = logs.filter(level=level_filter)
    
    if category_filter:
        logs = logs.filter(category=category_filter)
    
    if search:
        logs = logs.filter(
            models.Q(message__icontains=search) |
            models.Q(tag__icontains=search) |
            models.Q(exception_class__icontains=search)
        )
    
    # Límitar a los últimos 1000 logs para performance
    logs = logs[:1000]
    
    context = {
        'player': player,
        'logs': logs,
        'level_filter': level_filter,
        'category_filter': category_filter,
        'hours': hours,
        'search': search,
        'log_levels': DeviceLog.LOG_LEVELS,
        'log_categories': DeviceLog.CATEGORIES,
    }
    
    return render(request, 'players/device_logs_terminal.html', context)


def device_logs_api(request, device_id):
    """
    API endpoint para obtener logs de un dispositivo (para HTMX updates)
    """
    player = get_object_or_404(Player, device_id=device_id)
    
    level_filter = request.GET.get('level', '')
    hours = int(request.GET.get('hours', 1))
    
    #logs = player.get_recent_logs(hours=hours)
    logs = player.get_recent_logs(hours=hours).order_by('device_timestamp')
    
    if level_filter:
        logs = logs.filter(level=level_filter)
    
    logs = logs[:100]  # Últimos 100 logs
    
    logs_data = []
    for log in logs:
        logs_data.append({
            'timestamp': log.device_timestamp.strftime('%H:%M:%S.%f')[:-3],
            'level': log.level,
            'level_icon': log.level_icon,
            'level_color': log.level_color,
            'category': log.category,
            'category_icon': log.category_icon,
            'tag': log.tag,
            'message': log.message,
            'has_exception': log.has_exception,
            'thread_name': log.thread_name,
            'method_name': log.method_name,
        })
    
    return JsonResponse({
        'status': 'success',
        'logs': logs_data,
        'count': len(logs_data)
    })



def device_logs_redirect(request, pk):
    """Redirect from numeric ID to device_id for logs"""
    from django.shortcuts import get_object_or_404, redirect
    player = get_object_or_404(Player, pk=pk)
    return redirect('device_logs_terminal', device_id=player.device_id)







@csrf_exempt
@require_http_methods(["POST"])
def api_register_player(request):
    """
    API simple para registrar un player via curl
    
    POST /players/api/register/
    {
        "device_id": "A1B2C3D4E5F6G7H8",
        "name": "Test Player",
        "group_id": 1,  // opcional, usa grupo por defecto si no se especifica
        "app_version": "1.0.0",  // opcional
        "firmware_version": "12"  // opcional
    }
    """
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        name = data.get('name', f'Player {device_id[:8]}')
        group_id = data.get('group_id')
        
        if not device_id or len(device_id) != 16:
            return JsonResponse({
                'status': 'error',
                'message': 'device_id must be exactly 16 hexadecimal characters'
            }, status=400)
        
        # Verificar si ya existe
        if Player.objects.filter(device_id=device_id).exists():
            return JsonResponse({
                'status': 'error',
                'message': f'Player with device_id {device_id} already exists'
            }, status=400)
        
        # Obtener o crear grupo por defecto
        if group_id:
            try:
                group = Group.objects.get(id=group_id)
            except Group.DoesNotExist:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Group with id {group_id} does not exist'
                }, status=400)
        else:
            # Crear grupo por defecto si no existe
            group, created = Group.objects.get_or_create(
                name='Default Group',
                defaults={
                    'description': 'Default group for players',
                    'sync_interval': 300,
                    'resolution': '1920x1080',
                    'orientation': 'landscape',
                }
            )
        
        # Crear el player
        player = Player.objects.create(
            device_id=device_id,
            name=name,
            group=group,
            app_version=data.get('app_version', ''),
            firmware_version=data.get('firmware_version', ''),
            status='offline'
        )
        
        return JsonResponse({
            'status': 'success',
            'message': 'Player registered successfully',
            'player': {
                'id': player.id,
                'device_id': player.device_id,
                'name': player.name,
                'group': player.group.name,
                'status': player.status,
                'created_at': player.created_at.isoformat()
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON'
        }, status=400)
    
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Server error: {str(e)}'
        }, status=500)


# También agregar una vista GET para listar players registrados
@require_http_methods(["GET"])
def api_list_players(request):
    """Lista todos los players registrados"""
    players = Player.objects.all().select_related('group')
    
    players_data = []
    for player in players:
        players_data.append({
            'id': player.id,
            'device_id': player.device_id,
            'name': player.name,
            'group': player.group.name,
            'status': player.status,
            'last_sync': player.last_sync.isoformat() if player.last_sync else None,
            'app_version': player.app_version,
            'firmware_version': player.firmware_version,
            'battery_level': player.battery_level,
            'created_at': player.created_at.isoformat()
        })
    
    return JsonResponse({
        'status': 'success',
        'count': len(players_data),
        'players': players_data
    })