# scheduling/views.py - API de sincronización basada en el análisis del original
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.shortcuts import get_object_or_404
from players.models import Player, Group
from playlists.models import Playlist, PlaylistSchedule
from content.models import Asset
from .models import SyncRequest, EmergencyMessage, SystemCommand
import json
import hashlib
from datetime import datetime

@csrf_exempt
@require_http_methods(["POST"])
def device_check_server(request):
    """
    API principal de sincronización - reemplaza WebSocket del original
    
    Equivalente a la funcionalidad de sync del pisignage-server original
    """
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
                'status': 'device_not_registered',
                'server_timestamp': timezone.now().isoformat(),
                'message': 'Device not found in system'
            }, status=404)
        
        # Crear registro de sync request
        sync_request = SyncRequest.objects.create(
            player=player,
            client_sync_hash=data.get('last_sync_hash', ''),
            app_version=data.get('app_version', ''),
            firmware_version=data.get('firmware_version', ''),
            battery_level=data.get('battery_level'),
            storage_free_mb=data.get('storage_free_mb'),
            connection_type=data.get('connection_type', '')
        )
        
        # Actualizar información del player
        player.app_version = data.get('app_version', '')
        player.firmware_version = data.get('firmware_version', '')
        player.battery_level = data.get('battery_level')
        player.storage_free_mb = data.get('storage_free_mb')
        player.temperature_celsius = data.get('device_health', {}).get('temperature_celsius')
        player.signal_strength = data.get('device_health', {}).get('signal_strength')
        player.connection_type = data.get('connection_type', 'unknown')
        player.status = 'online'
        player.save()
        
        # Calcular hash actual del servidor para este player
        server_hash = calculate_player_sync_hash(player)
        client_hash = data.get('last_sync_hash', '')
        
        # Determinar si necesita sincronización
        needs_sync = (client_hash != server_hash)
        
        response = {
            'status': 'success',
            'server_timestamp': timezone.now().isoformat(),
            'device_registered': True,
            'needs_sync': needs_sync
        }
        
        # Verificar mensajes de emergencia
        emergency_messages = get_active_emergency_messages(player)
        if emergency_messages:
            response['emergency_messages'] = [msg.to_sync_data() for msg in emergency_messages]
        
        # Verificar comandos del sistema
        system_commands = get_pending_system_commands(player)
        if system_commands:
            response['system_commands'] = [cmd.to_sync_data() for cmd in system_commands]
        
        if needs_sync:
            # Generar datos de sincronización completos
            sync_data = generate_sync_data(player)
            response['sync_data'] = sync_data
            response['new_sync_hash'] = server_hash
            
            # Actualizar player con nuevo hash
            player.last_sync_hash = server_hash
            player.last_sync = timezone.now()
            player.reset_sync_failures()  # Reset failure counter on successful sync
            player.save()
            
            # Actualizar sync request
            sync_request.needs_sync = True
            sync_request.server_sync_hash = server_hash
        else:
            # No necesita sync
            response['next_check_interval'] = player.group.sync_interval
            
            sync_request.needs_sync = False
            sync_request.server_sync_hash = server_hash
        
        sync_request.response_timestamp = timezone.now()
        sync_request.save()
        
        return JsonResponse(response)
        
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


def calculate_player_sync_hash(player):
    """
    Calcular hash de sincronización para un player específico
    Basado en la lógica del original pero usando hash comparison
    """
    group = player.group
    
    # Obtener playlist activa para este player
    active_playlist = PlaylistSchedule.get_active_playlist_for_group(group)
    if not active_playlist:
        active_playlist = group.default_playlist
    
    sync_data = {
        'player_id': player.device_id,
        'group_config': {
            'sync_interval': group.sync_interval,
            'resolution': player.effective_resolution,
            'orientation': player.effective_orientation,
            'audio_enabled': group.audio_enabled,
            'tv_control': group.tv_control,
        },
        'playlist': None,
        'assets': []
    }
    
    if active_playlist:
        # Incluir datos de la playlist
        sync_data['playlist'] = {
            'id': active_playlist.id,
            'name': active_playlist.name,
            'layout': active_playlist.layout.code,
            'updated_at': active_playlist.updated_at.isoformat(),
            'ticker_enabled': active_playlist.ticker_enabled,
            'ticker_text': active_playlist.ticker_text,
        }
        
        # Incluir assets de la playlist con sus checksums
        for item in active_playlist.items.all().order_by('zone', 'order'):
            asset = item.asset
            sync_data['assets'].append({
                'id': asset.id,
                'name': asset.name,
                'checksum': asset.checksum or '',
                'updated_at': asset.updated_at.isoformat(),
                'duration': item.effective_duration,
                'zone': item.zone,
                'order': item.order
            })
    
    # Generar hash SHA256 del JSON
    json_string = json.dumps(sync_data, sort_keys=True)
    #return hashlib.sha256(json_string.encode()).hexdigest()
    full_hash = hashlib.sha256(json_string.encode()).hexdigest()
    return full_hash[:8]  # Primeros 8 caracteres


def generate_sync_data(player):
    """
    Generar datos completos de sincronización para un player
    Basado en el formato del original
    """
    group = player.group
    
    # Obtener playlist activa
    active_playlist = PlaylistSchedule.get_active_playlist_for_group(group)
    if not active_playlist:
        active_playlist = group.default_playlist
    
    sync_data = {
        'sync_id': f"sync_{timezone.now().strftime('%Y%m%d_%H%M%S')}",
        'sync_timestamp': timezone.now().isoformat(),
        'config_updates': {
            'sync_interval': group.sync_interval,
            'resolution': player.effective_resolution,
            'orientation': player.effective_orientation,
            'audio_enabled': group.audio_enabled,
            'tv_control': group.tv_control,
            'screenshot_interval': group.screenshot_interval,
        },
        'playlists': [],
        'assets': [],
        'deleted_assets': []  # TODO: Implementar tracking de assets eliminados
    }
    
    if active_playlist:
        # Convertir playlist a formato de sync
        playlist_data = active_playlist.to_sync_data()
        
        # Agregar horario si es una playlist programada
        current_schedule = None
        for schedule in active_playlist.schedules.filter(group=group, is_active=True):
            if schedule.is_active_now():
                current_schedule = schedule
                break
        
        if current_schedule:
            playlist_data['schedule'] = {
                'start_time': current_schedule.start_time.strftime('%H:%M'),
                'end_time': current_schedule.end_time.strftime('%H:%M'),
                'days_of_week': current_schedule.days_of_week,
                'priority': current_schedule.priority
            }
        
        sync_data['playlists'] = [playlist_data]
        
        # Recopilar todos los assets necesarios
        for item in active_playlist.items.all():
            asset = item.asset
            
            asset_data = {
                'id': str(asset.id),
                'name': asset.name,
                'type': asset.asset_type,
                'checksum': asset.checksum or '',
                'size_bytes': asset.file_size or 0,
                'metadata': {
                    'duration': asset.duration,
                    'resolution': asset.resolution,
                    'original_name': asset.original_name,
                }
            }
            
            # URLs de descarga
            if asset.file:
                asset_data['url'] = asset.download_url
            elif asset.url:
                asset_data['url'] = asset.url
            
            if asset.thumbnail:
                asset_data['thumbnail_url'] = asset.thumbnail_url
            
            # Agregar metadata específico del asset type
            if asset.metadata:
                asset_data['metadata'].update(asset.metadata)
            
            sync_data['assets'].append(asset_data)
    
    return sync_data


def get_active_emergency_messages(player):
    """Obtener mensajes de emergencia activos para un player"""
    from django.db import models
    now = timezone.now()
    
    messages = EmergencyMessage.objects.filter(
        is_active=True,
        start_time__lte=now
    ).filter(
        models.Q(end_time__isnull=True) | models.Q(end_time__gt=now)
    ).filter(
        models.Q(groups__in=[player.group]) | models.Q(players=player)
    ).distinct()
    
    return messages


def get_pending_system_commands(player):
    """Obtener comandos del sistema pendientes para un player"""
    commands = SystemCommand.objects.filter(
        status='pending',
        scheduled_at__lte=timezone.now(),
        players=player
    )
    
    return commands


@csrf_exempt
@require_http_methods(["POST"])
def device_sync_confirmation(request):
    """
    Confirmación de sincronización completada por el device
    """
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        sync_hash = data.get('sync_hash')
        
        player = get_object_or_404(Player, device_id=device_id)
        
        # Actualizar estado del player
        player.last_sync_hash = sync_hash
        player.last_sync = timezone.now()
        player.status = 'online'
        player.reset_sync_failures()
        player.save()
        
        # Registrar estadísticas de sync si se proporcionan
        if 'sync_stats' in data:
            stats = data['sync_stats']
            # TODO: Crear registro de SyncStats
        
        return JsonResponse({
            'status': 'success',
            'message': 'Sync confirmation received'
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt  
@require_http_methods(["POST"])
def emergency_message_acknowledgment(request):
    """
    Acknowledgment de mensaje de emergencia por parte del device
    """
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        message_id = data.get('message_id')
        
        player = get_object_or_404(Player, device_id=device_id)
        message = get_object_or_404(EmergencyMessage, id=message_id)
        
        # Crear acknowledgment
        from .models import EmergencyAcknowledgement
        EmergencyAcknowledgement.objects.get_or_create(
            emergency_message=message,
            player=player
        )
        
        return JsonResponse({
            'status': 'success',
            'message': 'Emergency message acknowledged'
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error', 
            'message': str(e)
        }, status=500)


# Asset download endpoint
@require_http_methods(["GET"])
def asset_download(request, asset_id):
    """
    Endpoint para descargar assets - usado durante sincronización
    """
    try:
        asset = get_object_or_404(Asset, id=asset_id)
        
        if not asset.file:
            return JsonResponse({
                'status': 'error',
                'message': 'File not available'
            }, status=404)
        
        # TODO: Implementar serving de archivos con nginx/apache en producción
        # Para desarrollo, Django puede servir el archivo directamente
        from django.http import FileResponse
        return FileResponse(
            asset.file.open('rb'),
            as_attachment=True,
            filename=asset.original_name or asset.name
        )
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@require_http_methods(["GET"])
def asset_thumbnail(request, asset_id):
    """
    Endpoint para descargar thumbnails de assets
    """
    try:
        asset = get_object_or_404(Asset, id=asset_id)
        
        if not asset.thumbnail:
            return JsonResponse({
                'status': 'error',
                'message': 'Thumbnail not available'
            }, status=404)
        
        from django.http import FileResponse
        return FileResponse(
            asset.thumbnail.open('rb'),
            as_attachment=False,
            filename=f"thumb_{asset.name}.jpg"
        )
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)