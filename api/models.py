from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    can_see_public_files = models.BooleanField(default=True)
