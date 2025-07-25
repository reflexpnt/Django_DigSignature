from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings as DjangoSETTINGs

def playlists_list(request):
    """Lista de playlists"""
    return HttpResponse("Playlists List - {DjangoSETTINGs.APP_NAME}")

def playlist_create(request):
    """Crear playlist"""
    return HttpResponse("Create Playlist - {DjangoSETTINGs.APP_NAME}")

def playlist_detail(request, pk):
    """Detalle de playlist"""
    return HttpResponse(f"Playlist Detail {pk} - {DjangoSETTINGs.APP_NAME}")

def playlist_edit(request, pk):
    """Editar playlist"""
    return HttpResponse(f"Edit Playlist {pk} - {DjangoSETTINGs.APP_NAME}")

def playlist_delete(request, pk):
    """Eliminar playlist"""
    return HttpResponse(f"Delete Playlist {pk} - {DjangoSETTINGs.APP_NAME}")

def playlist_duplicate(request, pk):
    """Duplicar playlist"""
    return HttpResponse(f"Duplicate Playlist {pk} - {DjangoSETTINGs.APP_NAME}")

def playlist_deploy(request, pk):
    """Desplegar playlist"""
    return HttpResponse(f"Deploy Playlist {pk} - {DjangoSETTINGs.APP_NAME}")

def playlist_preview(request, pk):
    """Preview de playlist"""
    return HttpResponse(f"Preview Playlist {pk} - {DjangoSETTINGs.APP_NAME}")

def playlist_item_add(request, playlist_pk):
    """Agregar item a playlist"""
    return HttpResponse(f"Add Item to Playlist {playlist_pk} - {DjangoSETTINGs.APP_NAME}")

def playlist_item_edit(request, playlist_pk, item_pk):
    """Editar item de playlist"""
    return HttpResponse(f"Edit Item {item_pk} in Playlist {playlist_pk} - {DjangoSETTINGs.APP_NAME}")

def playlist_item_delete(request, playlist_pk, item_pk):
    """Eliminar item de playlist"""
    return HttpResponse(f"Delete Item {item_pk} from Playlist {playlist_pk} - {DjangoSETTINGs.APP_NAME}")

def playlist_items_reorder(request, playlist_pk):
    """Reordenar items de playlist"""
    return HttpResponse(f"Reorder Items in Playlist {playlist_pk} - {DjangoSETTINGs.APP_NAME}")

def playlist_available_assets(request, pk):
    """API - Assets disponibles para playlist"""
    return HttpResponse(f"Available Assets for Playlist {pk} - {DjangoSETTINGs.APP_NAME}")