from django.shortcuts import render
from django.http import HttpResponse

def playlists_list(request):
    """Lista de playlists"""
    return HttpResponse("Playlists List - PiSignage")

def playlist_create(request):
    """Crear playlist"""
    return HttpResponse("Create Playlist - PiSignage")

def playlist_detail(request, pk):
    """Detalle de playlist"""
    return HttpResponse(f"Playlist Detail {pk} - PiSignage")

def playlist_edit(request, pk):
    """Editar playlist"""
    return HttpResponse(f"Edit Playlist {pk} - PiSignage")

def playlist_delete(request, pk):
    """Eliminar playlist"""
    return HttpResponse(f"Delete Playlist {pk} - PiSignage")

def playlist_duplicate(request, pk):
    """Duplicar playlist"""
    return HttpResponse(f"Duplicate Playlist {pk} - PiSignage")

def playlist_deploy(request, pk):
    """Desplegar playlist"""
    return HttpResponse(f"Deploy Playlist {pk} - PiSignage")

def playlist_preview(request, pk):
    """Preview de playlist"""
    return HttpResponse(f"Preview Playlist {pk} - PiSignage")

def playlist_item_add(request, playlist_pk):
    """Agregar item a playlist"""
    return HttpResponse(f"Add Item to Playlist {playlist_pk} - PiSignage")

def playlist_item_edit(request, playlist_pk, item_pk):
    """Editar item de playlist"""
    return HttpResponse(f"Edit Item {item_pk} in Playlist {playlist_pk} - PiSignage")

def playlist_item_delete(request, playlist_pk, item_pk):
    """Eliminar item de playlist"""
    return HttpResponse(f"Delete Item {item_pk} from Playlist {playlist_pk} - PiSignage")

def playlist_items_reorder(request, playlist_pk):
    """Reordenar items de playlist"""
    return HttpResponse(f"Reorder Items in Playlist {playlist_pk} - PiSignage")

def playlist_available_assets(request, pk):
    """API - Assets disponibles para playlist"""
    return HttpResponse(f"Available Assets for Playlist {pk} - PiSignage")