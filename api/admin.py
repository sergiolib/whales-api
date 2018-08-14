from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Permission
from . import models
from django.contrib import admin
admin.site.register(Permission)
admin.site.register(models.User, UserAdmin)
admin.site.register(models.Pipeline)