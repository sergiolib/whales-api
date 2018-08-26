from django.contrib.auth.models import AbstractUser
from django.db import models
from django_celery_results.models import TaskResult
from jsonfield import JSONField


class User(AbstractUser):
    can_see_public_files = models.BooleanField(default=True)


class Pipeline(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=1000)
    pipeline_type = models.CharField(max_length=100, blank=False)
    parameters = JSONField(blank=False, default={})
    task = models.ForeignKey(TaskResult, blank=True, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"{self.name} ({self.owner})"


class DataFile(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    location = models.CharField(max_length=5000)
    public = models.BooleanField(default=False)
    added_date = models.DateField(auto_now_add=True)
    formatter = models.CharField(max_length=100)
    data_file = models.CharField(max_length=100)


class LabelsFile(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    location = models.CharField(max_length=5000)
    public = models.BooleanField(default=False)
    added_date = models.DateField(auto_now_add=True)
    formatter = models.CharField(max_length=100)
