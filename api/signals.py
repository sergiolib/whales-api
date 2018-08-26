from api import models
from django.db.models.signals import post_init
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
