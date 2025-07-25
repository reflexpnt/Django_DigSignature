# Generated by Django 5.2.1 on 2025-07-24 08:24

import content.models
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Label',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
                ('color', models.CharField(default='#007bff', help_text='Hex color code (e.g., #007bff)', max_length=7)),
                ('description', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Label',
                'verbose_name_plural': 'Labels',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Layout',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True)),
                ('zones_config', models.JSONField(default=dict, help_text='JSON configuration for layout zones')),
                ('is_custom', models.BooleanField(default=False)),
                ('preview_image', models.ImageField(blank=True, null=True, upload_to='layouts/previews/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Layout',
                'verbose_name_plural': 'Layouts',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Asset',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('asset_type', models.CharField(choices=[('video', 'Video'), ('image', 'Image'), ('pdf', 'PDF'), ('html', 'HTML'), ('url', 'URL/Link'), ('audio', 'Audio')], max_length=10)),
                ('status', models.CharField(choices=[('uploading', 'Uploading'), ('processing', 'Processing'), ('ready', 'Ready'), ('error', 'Error')], default='ready', max_length=12)),
                ('file', models.FileField(blank=True, null=True, upload_to=content.models.asset_upload_path, validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['mp4', 'avi', 'mov', 'jpg', 'jpeg', 'png', 'pdf', 'html', 'zip', 'mp3', 'wav'])])),
                ('thumbnail', models.ImageField(blank=True, null=True, upload_to='thumbnails/%Y/%m/')),
                ('url', models.URLField(blank=True)),
                ('file_size', models.PositiveBigIntegerField(blank=True, null=True)),
                ('duration', models.PositiveIntegerField(blank=True, null=True)),
                ('resolution', models.CharField(blank=True, max_length=20)),
                ('description', models.TextField(blank=True)),
                ('version', models.PositiveIntegerField(default=1)),
                ('valid_from', models.DateTimeField(blank=True, null=True)),
                ('valid_until', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('labels', models.ManyToManyField(blank=True, to='content.label')),
            ],
            options={
                'verbose_name': 'Asset',
                'verbose_name_plural': 'Assets',
                'ordering': ['-created_at'],
            },
        ),
    ]
