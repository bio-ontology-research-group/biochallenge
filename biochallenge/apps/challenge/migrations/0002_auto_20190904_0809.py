# Generated by Django 2.2.5 on 2019-09-04 08:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('challenge', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='release',
            name='sparql_endpoint',
            field=models.CharField(default='aaa', max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='release',
            name='sparql_query',
            field=models.TextField(default='aaa'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='challenge',
            name='sparql_endpoint',
            field=models.CharField(max_length=255),
        ),
    ]
