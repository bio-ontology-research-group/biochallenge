# Generated by Django 2.2.17 on 2021-01-20 10:54

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_auto_20201214_0727'),
        ('challenge', '0008_submission_hits_10'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='submission',
            name='user',
        ),
        migrations.AddField(
            model_name='submission',
            name='team',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='submissions', to='accounts.Team'),
        ),
    ]
