import json
from base64 import b64encode
from glob import glob
from mimetypes import guess_type
from os import rename
from os.path import join, basename
from shutil import copytree, copy

from django.conf import settings
from django.db.models import QuerySet
from rest_framework import authentication, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from api import models
from api import getters
from api.models import LaunchPipelineTask


class UsersPipelinesView(APIView):
    authentication_classes = (authentication.BasicAuthentication, authentication.TokenAuthentication)
    permission_classes = (permissions.BasePermission,)

    def get(self, request):
        private_pipelines = models.Pipeline.objects.none()
        public_pipelines = models.Pipeline.objects.none()
        try:
            private_pipelines = models.Pipeline.objects.filter(owner=request.user)
        except:
            pass
        try:
            public_pipelines = models.Pipeline.objects.filter(public=True)
        except:
            pass
        q = (private_pipelines | public_pipelines).distinct()
        q = [{'name': i.name, 'parameters': i.parameters, 'type': i.pipeline_type, "public": i.public, "owner": i.owner.email, "created_on": i.created_on} for i in q]
        q = sorted(q, key=lambda x: x["created_on"])
        q.reverse()
        [i.update({"created_on": i["created_on"].strftime("%Y-%m-%d %H:%M:%S %Z")}) for i in q]
        return Response(data=q)


class UsersPipelinesCreateView(APIView):
    def post(self, request):
        desired_name = request.data["new_pipeline_name"]
        desired_type = request.data["new_pipeline_type"]
        # Check it doesn't exist yet
        q = models.Pipeline.objects.filter(name=desired_name)
        if len(q) > 0:
            return Response(data="Pipeline with that name already exists", status=400)

        # Create new pipeline
        default_parameters = getters.GettersData("pipelines").to_list()
        default_parameters = [i["parameters"] for i in default_parameters if i["description"] == desired_type][0]
        pip = models.Pipeline(
            owner=request.user,
            name=desired_name,
            pipeline_type=desired_type,
            parameters=default_parameters
        )
        pip.parameters["trained_model_pipeline"] = {"value": ""}
        pip.save()
        return Response()


class UsersPipelinesDeleteView(APIView):
    def delete(self, request):
        try:
            pipeline_name = request.query_params["pipeline_name"]
            q = models.Pipeline.objects.get(owner=request.user, name=pipeline_name)
        except models.Pipeline.DoesNotExist:
            return Response(data=f"Pipeline named {pipeline_name} owned by {request.user.email} does not exist", status=401)
        except KeyError:
            return Response(data=f"Pipeline name not submitted in the request", status=402)
        q.delete()
        return Response()


class UsersPipelinesPublicView(APIView):
    def post(self, request):
        try:
            pipeline_name = request.query_params["pipeline_name"]
            q = models.Pipeline.objects.get(owner=request.user, name=pipeline_name)
        except models.Pipeline.DoesNotExist:
            return Response(data=f"Pipeline named {pipeline_name} does not exist", status=401)
        except KeyError:
            return Response(data=f"Pipeline name not submitted in the request", status=402)
        q.public = request.data["public"]
        q.save()
        return Response()


class UsersPipelinesLoadParameterView(APIView):
    def get(self, request, parameter):
        if "pipeline_name" not in request.query_params:
            return Response(data=f"Pipeline name not submitted in the request", status=401)

        pipeline_name = request.query_params["pipeline_name"]

        try:
            q = models.Pipeline.objects.get(owner=request.user, name=pipeline_name)
        except models.Pipeline.DoesNotExist:
            return Response(data=f"Pipeline named {pipeline_name} does not exist", status=401)

        if parameter not in q.parameters:
            return Response("Parameter not understood", status=401)

        return Response(q.parameters[parameter])


class UsersPipelinesSaveParameterView(APIView):
    def post(self, request, parameter):
        try:
            pipeline_name = request.query_params['pipeline_name']
            q = models.Pipeline.objects.get(owner=request.user, name=pipeline_name)
        except models.Pipeline.DoesNotExist:
            return Response(data=f"Pipeline named {pipeline_name} does not exist", status=401)
        except KeyError:
            return Response(data=f"Pipeline name not submitted in the request", status=402)

        assert parameter in q.parameters  # the parameter should exist already in the object

        try:
            q.parameters[parameter] = {
                "type": request.data.get("type", ""),
                "value": request.data["value"],
                "options": request.data.get("options", [])
            }
        except KeyError:
            return Response()

        if parameter == "trained_model_pipeline":
            training_pipeline_name = request.data["value"]
            training_q = models.Pipeline.objects.get(owner=request.user, name=training_pipeline_name)

            trained_models = glob(join(training_q.models_directory(), "*"))
            for tf in trained_models:
                copy(tf, q.models_directory())
            # ML
            q.parameters["machine_learning"] = training_q.parameters["machine_learning"]
            # FE
            q.parameters["features_extractors"] = training_q.parameters["features_extractors"]
            # PP
            q.parameters["pre_processing"] = training_q.parameters["pre_processing"]

            # This instruction setting
            q.parameters["trained_model_pipeline"] = {"value": training_pipeline_name}

        q.save()

        return Response()


class UsersPipelinesDuplicateView(APIView):
    def post(self, request):
        try:
            pipeline_name = request.data['pipeline_name']
            owner = request.data['pipeline_owner']
            owner = models.User.objects.get(email=owner)
            q = models.Pipeline.objects.get(owner=owner, name=pipeline_name)
        except models.Pipeline.DoesNotExist:
            return Response(data=f"Pipeline named {pipeline_name} owned by {owner.email} does not exist", status=401)
        except KeyError:
            return Response(data=f"Pipeline name not submitted in the request", status=402)
        original_results_directory = q.results_directory()
        original_logs_directory = q.logs_directory()
        modifier = ""
        while len(models.Pipeline.objects.filter(name=q.name + "_duplicate" + modifier)) > 0:
            modifier = modifier + "0"
        new_q = models.Pipeline(name=q.name + "_duplicate" + modifier, owner=request.user, parameters=q.parameters, pipeline_type=q.pipeline_type)
        new_results_directory = new_q.results_directory()
        new_logs_directory = new_q.logs_directory()
        copytree(original_logs_directory, new_logs_directory)
        copytree(original_results_directory, new_results_directory)
        new_q.save()
        return Response()


class UsersPipelinesRenameView(APIView):
    def post(self, request):
        try:
            pipeline_name = request.data['pipeline_name']
            q = models.Pipeline.objects.get(owner=request.user, name=pipeline_name)
        except models.Pipeline.DoesNotExist:
            return Response(data=f"Pipeline named {pipeline_name} does not exist", status=401)
        except KeyError:
            return Response(data=f"Pipeline name not submitted in the request", status=402)
        original_results_directory = q.results_directory()
        original_logs_directory = q.logs_directory()
        q.name = request.data["new_pipeline_name"]
        new_results_directory = q.results_directory()
        new_logs_directory = q.logs_directory()
        rename(original_logs_directory, new_logs_directory)
        rename(original_results_directory, new_results_directory)
        q.save()
        return Response()


def transform_parameters(parameters):
    new_params = {}
    data_files_directory = join(settings.MEDIA_ROOT, "{owner}", "data_files")
    labels_files_directory = join(settings.MEDIA_ROOT, "{owner}", "labels_files")
    for i in parameters:
        if i == "input_data":
            input_data = parameters[i]["value"]
            new_input_data = []
            for j in input_data:
                new_input_data.append({
                    "file_name": join(data_files_directory.format(owner=j['owner']), j["name"]),
                    "data_file": "audio",
                    "formatter": "aif"
                })
            new_params[i] = new_input_data
        elif i == "input_labels":
            input_labels = parameters[i]["value"]
            new_input_labels = []
            for j in input_labels:
                new_input_labels.append({
                    "labels_file": join(labels_files_directory.format(owner=j['owner']), j["name"]),
                    "labels_formatter": "csv"
                })
            new_params[i] = new_input_labels
        elif i == "machine_learning":
            new_params[i] = parameters[i]["value"]
        elif i == "pre_processing" or i == "features_extractors" or i == "performance_indicators":
            original = parameters[i]["value"]
            new = []
            for j in original:
                params = j["parameters"]
                new.append({
                    "method": j["method"],
                    "parameters": {a: params[a]['value'] for a in params}
                })
            new_params[i] = new
    return new_params


class UsersPipelinesProcessView(APIView):
    def post(self, request):
        """Launch a new pipeline. Reuse task object if possible"""
        try:
            pipeline_name = request.data['pipeline_name']
            q = models.Pipeline.objects.get(owner=request.user, name=pipeline_name)
        except models.Pipeline.DoesNotExist:
            return Response(data=f"Pipeline named {pipeline_name} does not exist", status=401)
        except KeyError:
            return Response(data=f"Pipeline name not submitted in the request", status=402)

        # Try to get the task object from DB, but only if it is in FINISHED or FAILURE status
        parameters = transform_parameters(q.parameters)
        task = LaunchPipelineTask.objects.get_or_create(
            pipeline=q
        )[0]
        task.pipeline_parameters = json.dumps(parameters)
        task.pipeline_desc = q.pipeline_type
        task.results_directory = q.results_directory()
        task.logs_directory = q.logs_directory()
        task.job_id = ""
        task.failure_reason = ""
        task.save()
        task.run(is_async=False)

        q.task = task
        q.save()

        return Response()

    def get(self, request):
        """Get the pipeline state"""
        try:
            pipeline_name = request.query_params['pipeline_name']
            q = models.Pipeline.objects.get(owner=request.user, name=pipeline_name)
        except models.Pipeline.DoesNotExist:
            return Response(data=f"Pipeline named {pipeline_name} does not exist", status=401)
        except KeyError:
            return Response(data=f"Pipeline name not submitted in the request", status=402)
        try:
            task_result = LaunchPipelineTask.objects.get(pipeline=q)
        except LaunchPipelineTask.DoesNotExist:
            return Response(data=(0, ""))
        if task_result.job_id is None:
            return Response(data=(0, ""))
        elif task_result.status == "SUCCESS":
            return Response(data=(3, ""))
        elif task_result.status == "FAILURE":
            return Response(data=(2, task_result.failure_reason))
        elif task_result.status == "STARTED":
            if len(task_result.failure_reason) > 0:
                return Response(data=(2, task_result.failure_reason))
            else:
                return Response(data=(1, ""))
        elif task_result.status == "PENDING":
            return Response(data=(1, ""))


class UsersPipelinesLogsView(APIView):
    def get(self, request):
        """Get the pipeline logs files"""
        try:
            pipeline_name = request.query_params['pipeline_name']
            q = models.Pipeline.objects.get(owner=request.user, name=pipeline_name)
        except models.Pipeline.DoesNotExist:
            return Response(data=f"Pipeline named {pipeline_name} does not exist", status=401)
        except KeyError:
            return Response(data=f"Pipeline name not submitted in the request", status=402)
        ld = q.logs_directory()
        elements = glob(join(ld, "*"))
        contents = []
        for e in elements:
            with open(e, 'r') as f:
                contents.append(f.read().replace("\n", "<br />"))
        elements = [{"name": basename(e), "content": c} for e, c in zip(elements, contents)]
        return Response(elements)


class UsersPipelinesResultsView(APIView):
    def get(self, request):
        """Get the pipeline results files"""
        try:
            pipeline_name = request.query_params['pipeline_name']
            q = models.Pipeline.objects.get(owner=request.user, name=pipeline_name)
        except models.Pipeline.DoesNotExist:
            return Response(data=f"Pipeline named {pipeline_name} does not exist", status=401)
        except KeyError:
            return Response(data=f"Pipeline name not submitted in the request", status=402)
        rd = q.results_directory()
        elements = glob(join(rd, "*"))
        contents = []
        for e in elements:
            mime = guess_type(e)[0]
            if mime is not None:
                if "image" in mime:
                    with open(e, 'rb') as f:
                        data = b64encode(f.read()).decode('utf-8').replace('\n', '')
                        data_url = f"data:{mime};base64,{data}"
                        contents.append(data_url)
                elif "text" in mime:
                    with open(e, 'r') as f:
                        contents.append(f.read())

        elements = [{"name": basename(e), "content": c} for e, c in zip(elements, contents)]
        return Response(elements)
