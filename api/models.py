from django.contrib.auth.models import AbstractUser
from django.db import models
from jsonfield import JSONField


class User(AbstractUser):
    can_see_public_files = models.BooleanField(default=True)


class Pipeline(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=1000)
    pipeline_type = models.CharField(max_length=100, blank=False)
    parameters = JSONField(blank=False)

    def __str__(self):
        return f"{self.name} ({self.owner})"
