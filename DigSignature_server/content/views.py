from django.shortcuts import render
from django.http import HttpResponse

def assets_list(request):
    """Lista de assets"""
    return HttpResponse("Assets List - PiSignage")

def asset_upload(request):
    """Subir assets"""
    return HttpResponse("Asset Upload - PiSignage")

def asset_add_link(request):
    """Agregar link/URL"""
    return HttpResponse("Add Link - PiSignage")

def asset_detail(request, pk):
    """Detalle de asset"""
    return HttpResponse(f"Asset Detail {pk} - PiSignage")

def asset_edit(request, pk):
    """Editar asset"""
    return HttpResponse(f"Edit Asset {pk} - PiSignage")

def asset_delete(request, pk):
    """Eliminar asset"""
    return HttpResponse(f"Delete Asset {pk} - PiSignage")

def asset_download(request, pk):
    """Descargar asset"""
    return HttpResponse(f"Download Asset {pk} - PiSignage")

def labels_list(request):
    """Lista de labels"""
    return HttpResponse("Labels List - PiSignage")

def label_create(request):
    """Crear label"""
    return HttpResponse("Create Label - PiSignage")

def label_edit(request, pk):
    """Editar label"""
    return HttpResponse(f"Edit Label {pk} - PiSignage")

def label_delete(request, pk):
    """Eliminar label"""
    return HttpResponse(f"Delete Label {pk} - PiSignage")

def layouts_list(request):
    """Lista de layouts"""
    return HttpResponse("Layouts List - PiSignage")

def layout_create(request):
    """Crear layout"""
    return HttpResponse("Create Layout - PiSignage")

def layout_detail(request, pk):
    """Detalle de layout"""
    return HttpResponse(f"Layout Detail {pk} - PiSignage")

def layout_edit(request, pk):
    """Editar layout"""
    return HttpResponse(f"Edit Layout {pk} - PiSignage")

def layout_delete(request, pk):
    """Eliminar layout"""
    return HttpResponse(f"Delete Layout {pk} - PiSignage")

def upload_progress(request, upload_id):
    """API para progreso de upload"""
    return HttpResponse(f"Upload Progress {upload_id} - PiSignage")