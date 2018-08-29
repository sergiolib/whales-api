from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Permission
from . import models
from django.contrib import admin

admin.site.register(Permission)
admin.site.register(models.User, UserAdmin)
admin.site.register(models.Pipeline)
admin.site.register(models.DataFile)
admin.site.register(models.LabelsFile)
admin.site.register(models.LaunchPipelineTask)
