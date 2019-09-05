# Generated by Django 2.2.5 on 2019-09-05 02:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('challenge', '0004_release_version'),
    ]

    operations = [
        migrations.AddField(
            model_name='submission',
            name='status',
            field=models.CharField(default='evaluation', max_length=31),
        ),
        migrations.AlterField(
            model_name='challenge',
            name='status',
            field=models.CharField(choices=[('draft', 'draft'), ('active', 'active'), ('updating', 'updating'), ('update_failed', 'update_failed'), ('withdrawn', 'withdrawn')], max_length=15),
        ),
    ]
