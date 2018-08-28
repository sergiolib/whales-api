import json

from django_task.job import Job
import sys


class LaunchPipelineJob(Job):
    @staticmethod
    def execute(job, task):
        sys.path.append("../ballenas/src")
        from whales.modules.pipelines import getters as backend_getters
        params = task.retrieve_params_as_dict()
        pipeline_desc = params["pipeline_desc"]
        pipeline = params["pipeline"]
        pipeline_parameters = json.loads(params["pipeline_parameters"])
        results_directory = pipeline.results_directory()
        logs_directory = pipeline.logs_directory()
        models_directory = pipeline.models_directory()
        av = backend_getters.get_available_pipelines()
        for pipeline_type, pipeline_cls in av.items():
            p = pipeline_cls()
            if pipeline_cls().description == pipeline_desc:
                break
        pipeline_parameters["results_directory"] = results_directory
        pipeline_parameters["logs_directory"] = logs_directory
        pipeline_parameters["models_directory"] = models_directory
        p.load_parameters(pipeline_parameters)
        p.initialize()
        p.start()
