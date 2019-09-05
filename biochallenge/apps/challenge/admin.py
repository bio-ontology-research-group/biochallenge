from django.contrib import admin
from challenge import models

# Register your models here.
admin.site.register(models.Challenge)
admin.site.register(models.Release)
admin.site.register(models.Submission)
