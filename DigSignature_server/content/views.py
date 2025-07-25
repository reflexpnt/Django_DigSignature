from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, FileResponse, Http404
from django.views.decorators.http import require_http_methods
from django.utils.encoding import smart_str
from .models import Asset
import os
import mimetypes

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

@require_http_methods(["GET"])
def asset_download(request, pk):
    """
    Descargar asset - Implementación real para servir archivos
    """
    try:
        # Obtener el asset
        asset = get_object_or_404(Asset, pk=pk)
        
        # Verificar que tiene archivo
        if not asset.file:
            if asset.url:
                # Es un link/URL - redirigir
                from django.shortcuts import redirect
                return redirect(asset.url)
            else:
                return HttpResponse(
                    f"Asset '{asset.name}' has no file or URL",
                    status=404,
                    content_type='text/plain'
                )
        
        # Verificar que el archivo existe físicamente
        if not os.path.exists(asset.file.path):
            return HttpResponse(
                f"File not found: {asset.file.name}",
                status=404,
                content_type='text/plain'
            )
        
        # Obtener información del archivo
        file_path = asset.file.path
        file_size = os.path.getsize(file_path)
        
        # Determinar nombre de descarga
        download_name = asset.original_name or asset.name
        if not download_name.lower().endswith(('.mp4', '.avi', '.mov', '.jpg', '.png', '.pdf', '.html', '.zip', '.mp3')):
            # Agregar extensión basada en el tipo
            ext_map = {
                'video': '.mp4',
                'image': '.jpg',
                'audio': '.mp3',
                'pdf': '.pdf',
                'html': '.html',
                'zip': '.zip'
            }
            if asset.asset_type in ext_map:
                download_name += ext_map[asset.asset_type]
        
        # Determinar content type
        content_type, _ = mimetypes.guess_type(file_path)
        if not content_type:
            content_type = 'application/octet-stream'
        
        # Log de descarga para debugging
        print(f"📥 Serving asset download: {asset.name}")
        print(f"   File: {file_path}")
        print(f"   Size: {file_size} bytes")
        print(f"   Content-Type: {content_type}")
        print(f"   Download name: {download_name}")
        
        # Crear respuesta de archivo
        try:
            response = FileResponse(
                open(file_path, 'rb'),
                as_attachment=True,
                filename=smart_str(download_name),
                content_type=content_type
            )
            
            # Headers adicionales
            response['Content-Length'] = file_size
            response['Content-Disposition'] = f'attachment; filename="{smart_str(download_name)}"'
            
            # Cache headers para assets (pueden ser cacheados)
            response['Cache-Control'] = 'public, max-age=3600'  # 1 hora
            
            return response
            
        except IOError:
            return HttpResponse(
                f"Error reading file: {asset.file.name}",
                status=500,
                content_type='text/plain'
            )
            
    except Asset.DoesNotExist:
        return HttpResponse(
            f"Asset with ID {pk} not found",
            status=404,
            content_type='text/plain'
        )
    except Exception as e:
        # Log del error para debugging
        print(f"❌ Error serving asset {pk}: {e}")
        return HttpResponse(
            f"Server error: {str(e)}",
            status=500,
            content_type='text/plain'
        )

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