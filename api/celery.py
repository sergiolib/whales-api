import os
import sys
from os.path import join

from celery import Celery
from django.conf import settings

sys.path.append("../ballenas/src")

from whales.modules.pipelines import getters as backend_getters


# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'whales_api.settings')

app = Celery('api')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


@app.task(name="launch-pipeline")
def launch_pipeline(pipeline_desc, pipeline_parameters, output_directoy):
    av = backend_getters.get_available_pipelines()
    for pipeline_type, pipeline_cls in av.items():
        p = pipeline_cls()
        if pipeline_cls().description == pipeline_desc:
            break
    pipeline_parameters = fix_pipeline_parameters(pipeline_parameters)
    pipeline_parameters["output_directory"] = output_directoy
    p.load_parameters(pipeline_parameters)
    p.initialize()
    p.start()


def fix_pipeline_parameters(pipeline_parameters):
    for i in pipeline_parameters:
        params = pipeline_parameters[i]
        if i == "machine_learning":
            pipeline_parameters[i] = fix_machine_learning_parameters(params)
        elif i in ['features_extractors', 'pre_processing', 'performance_indicators']:
            pipeline_parameters[i] = fix_listed_parameters(params)
        elif i == 'input_data':
            pipeline_parameters[i] = fix_input_data(params)
        elif i == 'input_labels':
            pipeline_parameters[i] = fix_input_labels(params)
        else:
            pipeline_parameters[i] = params['value']
    return pipeline_parameters


def fix_machine_learning_parameters(machine_learning_parameters):
    if len(machine_learning_parameters['value']) == 0:
        return {}
    new_params = {
        'method': machine_learning_parameters['value']['name'],
        'type': machine_learning_parameters['value']['type'],
        'parameters': fix_lower_level_parameters(machine_learning_parameters['value']['parameters'])
    }
    return new_params


def fix_listed_parameters(parameters):
    ret = []
    for i in parameters['value']:
        ret.append({
            'method': i['name'],
            'parameters': fix_lower_level_parameters(i['parameters'])
        })
    return ret


def fix_lower_level_parameters(lower_level_parameters):
    new_params = {}
    for i in lower_level_parameters:
        if 'value' in lower_level_parameters[i]:
            new_params[i] = lower_level_parameters[i]['value']
    return new_params


def fix_input_data(parameters):
    ret = []
    for f in parameters['value']:
        location = join(settings.MEDIA_ROOT, f['owner'], "data_files", f['name'])
        data_file = 'audio'
        formatter = 'aif'
        ret.append({
            "file_name": location,
            "data_file": data_file,
            "formatter": formatter,
        })
    return ret


def fix_input_labels(parameters):
    ret = []
    for f in parameters['value']:
        location = join(settings.MEDIA_ROOT, f['owner'], "labels_files", f['name'])
        formatter = 'csv'
        ret.append({
            "labels_file": location,
            "labels_formatter": formatter,
        })
    return ret
