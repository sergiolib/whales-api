from os import makedirs
from shutil import rmtree

from api import models
from django.db.models.signals import post_init, pre_save, pre_delete
from django.dispatch import receiver
from api import getters


@receiver(post_init, sender=models.Pipeline)
def pipeline_default_parameters(sender, instance, **kwargs):
    if instance.parameters == {}:
        default_parameters = getters.GettersData("pipelines").to_list()
        default_parameters = [i["parameters"]
                              for i in default_parameters
                              if i["description"] == instance.pipeline_type]
        if len(default_parameters) == 0:
            raise AttributeError("Pipeline's description doesn't match any known pipeline type")
        instance.parameters.update(default_parameters[0])


@receiver(pre_save, sender=models.Pipeline)
def pipeline_create_results_dir(sender, instance, *args, **kwargs):
    makedirs(instance.results_directory(), exist_ok=True)


@receiver(pre_save, sender=models.Pipeline)
def pipeline_create_logs_dir(sender, instance, *args, **kwargs):
    makedirs(instance.logs_directory(), exist_ok=True)


@receiver(pre_save, sender=models.Pipeline)
def pipeline_create_logs_dir(sender, instance, *args, **kwargs):
    makedirs(instance.models_directory(), exist_ok=True)


@receiver(pre_delete, sender=models.Pipeline)
def pipeline_delete_dirs(sender, instance, **kwargs):
    try:
        rmtree(instance.logs_directory())
    except FileNotFoundError:
        pass
    try:
        rmtree(instance.models_directory())
    except FileNotFoundError:
        pass
    try:
        rmtree(instance.results_directory())
    except FileNotFoundError:
        pass
