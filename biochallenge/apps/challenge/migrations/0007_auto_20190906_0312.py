# Generated by Django 2.2.5 on 2019-09-06 03:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('challenge', '0006_challenge_script'),
    ]

    operations = [
        migrations.AlterField(
            model_name='challenge',
            name='script',
            field=models.CharField(choices=[('updater/Challenge.groovy', 'updater/Challenge.groovy'), ('updater/Challenge.groovy', 'updater/ChallengeUniprot.groovy')], default='updater/Challenge.groovy', max_length=31),
        ),
    ]
