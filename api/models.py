import datetime
from os.path import join

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django_task.models import Task
from jsonfield import JSONField


class User(AbstractUser):
    can_see_public_files = models.BooleanField(default=True)


class Pipeline(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=1000)
    pipeline_type = models.CharField(max_length=100, blank=False)
    parameters = JSONField(blank=False, default={})
    public = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.owner})"

    def results_directory(self):
        return join(settings.MEDIA_ROOT, self.owner.username, "results", self.name)

    def logs_directory(self):
        return join(settings.MEDIA_ROOT, self.owner.username, "logs", self.name)

    def models_directory(self):
        return join(settings.MEDIA_ROOT, self.owner.username, "models", self.name)


class LaunchPipelineTask(Task):
    TASK_QUEUE = "default"
    TASK_TIMEOUT = 3600
    LOG_TO_FIELD = True
    LOG_TO_FILE = False
    DEFAULT_VERBOSITY = 2

    pipeline_parameters = models.CharField(max_length=10000, default="{}")
    pipeline_desc = models.CharField(max_length=1000, default="")
    pipeline = models.ForeignKey(Pipeline, on_delete=models.CASCADE)

    @staticmethod
    def get_jobfunc():
        from .jobs import LaunchPipelineJob
        return LaunchPipelineJob


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
