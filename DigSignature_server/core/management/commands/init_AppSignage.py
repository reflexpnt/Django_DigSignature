# core/management/commands/init_AppSignage.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from content.models import Layout, Label
from players.models import Group
from playlists.models import Playlist
from django.conf import settings as DjangoSETTINGs


class Command(BaseCommand):
    help = 'Initialize {DjangoSETTINGs.APP_NAME} system with default data'
    
    def handle(self, *args, **options):
        self.stdout.write('Initializing {DjangoSETTINGs.APP_NAME} system...')
        
        # 1. Crear layouts por defecto
        self.stdout.write('Creating default layouts...')
        Layout.get_default_layouts()
        self.stdout.write(self.style.SUCCESS('✓ Default layouts created'))
        
        # 2. Crear labels por defecto
        self.stdout.write('Creating default labels...')
        default_labels = [
            {'name': 'Video', 'color': '#dc3545'},
            {'name': 'Image', 'color': '#28a745'},
            {'name': 'Audio', 'color': '#ffc107'},
            {'name': 'Urgent', 'color': '#fd7e14'},
            {'name': 'Promotion', 'color': '#20c997'},
            {'name': 'Information', 'color': '#17a2b8'},
        ]
        
        for label_data in default_labels:
            label, created = Label.objects.get_or_create(
                name=label_data['name'],
                defaults={'color': label_data['color']}
            )
            if created:
                self.stdout.write(f'  ✓ Created label: {label.name}')
        
        # 3. Crear grupo por defecto
        self.stdout.write('Creating default group...')
        default_group, created = Group.objects.get_or_create(
            name='Default Group',
            defaults={
                'description': 'Default group for new players',
                'sync_interval': 300,
                'resolution': '1920x1080',
                'orientation': 'landscape',
                'audio_enabled': True,
                'tv_control': False,
                'screenshot_interval': 3600,
                'default_timezone': 'UTC'
            }
        )
        if created:
            self.stdout.write(f'  ✓ Created group: {default_group.name}')
        else:
            self.stdout.write(f'  - Group already exists: {default_group.name}')
        
        # 4. Crear playlist por defecto
        self.stdout.write('Creating default playlist...')
        try:
            layout_1 = Layout.objects.get(code='1')  # Full screen layout
            
            default_playlist, created = Playlist.objects.get_or_create(
                name='Welcome Playlist',
                defaults={
                    'description': 'Default welcome playlist for new installations',
                    'layout': layout_1,
                    'ticker_enabled': True,
                    'ticker_text': 'Welcome to {DjangoSETTINGs.APP_NAME} Digital Signage System',
                    'ticker_speed': 5,
                    'shuffle_enabled': False,
                    'repeat_enabled': True
                }
            )
            
            if created:
                self.stdout.write(f'  ✓ Created playlist: {default_playlist.name}')
                
                # Asignar playlist al grupo por defecto
                default_group.default_playlist = default_playlist
                default_group.save()
                self.stdout.write(f'  ✓ Assigned playlist to {default_group.name}')
            else:
                self.stdout.write(f'  - Playlist already exists: {default_playlist.name}')
                
        except Layout.DoesNotExist:
            self.stdout.write(self.style.ERROR('  ✗ Layout "1" not found. Run migrations first.'))
        
        # 5. Verificar configuración del sistema
        self.stdout.write('Checking system configuration...')
        from core.models import SystemSettings
        settings = SystemSettings.get_settings()
        self.stdout.write(f'  ✓ System settings initialized: {settings.installation_name}')
        
        # 6. Mostrar resumen
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('{DjangoSETTINGs.APP_NAME} initialization completed!'))
        self.stdout.write('='*50)
        
        # Estadísticas
        layout_count = Layout.objects.count()
        label_count = Label.objects.count()
        group_count = Group.objects.count()
        playlist_count = Playlist.objects.count()
        
        self.stdout.write(f'📊 System Summary:')
        self.stdout.write(f'   • Layouts: {layout_count}')
        self.stdout.write(f'   • Labels: {label_count}')
        self.stdout.write(f'   • Groups: {group_count}')
        self.stdout.write(f'   • Playlists: {playlist_count}')
        
        self.stdout.write('\n🚀 Next steps:')
        self.stdout.write('   1. Run: python manage.py runserver')
        self.stdout.write('   2. Visit: http://localhost:8000/admin/')
        self.stdout.write('   3. Login with admin credentials')
        self.stdout.write('   4. Upload assets in Content → Assets')
        self.stdout.write('   5. Register players via API or admin')
        
        self.stdout.write('\n📱 Test device registration:')
        self.stdout.write('   curl -X POST "http://localhost:8000/players/api/register/" \\')
        self.stdout.write('        -H "Content-Type: application/json" \\')
        self.stdout.write('        -d \'{"device_id":"A1B2C3D4E5F6G7H8","name":"Test Player"}\'')
        
        self.stdout.write('\n📡 Test sync check:')  
        self.stdout.write('   curl -X POST "http://localhost:8000/scheduling/api/v1/device/check_server/" \\')
        self.stdout.write('        -H "Content-Type: application/json" \\')
        self.stdout.write('        -d \'{"device_id":"A1B2C3D4E5F6G7H8","last_sync_hash":""}\'')
        
        self.stdout.write(self.style.SUCCESS('\n✅ {DjangoSETTINGs.APP_NAME} Django port is ready!'))
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Reset all default data (WARNING: This will delete existing data)',
        )
    
    def handle_reset(self):
        """Reset all default data - use with caution"""
        self.stdout.write(self.style.WARNING('⚠️ RESETTING ALL DEFAULT DATA...'))
        
        # Confirmar acción
        confirm = input('This will delete existing layouts, labels, and default group. Continue? (yes/no): ')
        if confirm.lower() != 'yes':
            self.stdout.write('Reset cancelled.')
            return
        
        # Eliminar datos
        Layout.objects.filter(is_custom=False).delete()
        Label.objects.filter(name__in=['Video', 'Image', 'Audio', 'Urgent', 'Promotion', 'Information']).delete()
        Group.objects.filter(name='Default Group').delete()
        Playlist.objects.filter(name='Welcome Playlist').delete()
        
        self.stdout.write(self.style.SUCCESS('✓ Default data reset completed'))