from os import makedirs
from os.path import join

from django.conf import settings
from django_celery_results.models import TaskResult
from rest_framework.response import Response
from rest_framework.views import APIView
from api import models
from api import getters


class UsersPipelinesView(APIView):
    def get(self, request):
        if request.user.is_anonymous:
            return Response(f"Must login to be able to see the user's pipelines", status=400)
        q = models.Pipeline.objects.filter(owner=request.user)
        q = [{'name': i.name, 'parameters': i.parameters, 'type': i.pipeline_type} for i in q]
        return Response(data=q)


class UsersPipelinesCreateView(APIView):
    def post(self, request):
        desired_name = request.data["new_pipeline_name"]
        desired_type = request.data["new_pipeline_type"]
        # Check it doesn't exist yet
        q = models.Pipeline.objects.filter(owner=request.user, name=desired_name)
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
        pip.save()
        return Response()


class UsersPipelinesDeleteView(APIView):
    def delete(self, request):
        try:
            pipeline_name = request.query_params["pipeline_name"]
            q = models.Pipeline.objects.get(owner=request.user, name=pipeline_name)
        except models.Pipeline.DoesNotExist:
            return Response(data=f"Pipeline named {pipeline_name} does not exist", status=401)
        except KeyError:
            return Response(data=f"Pipeline name not submitted in the request", status=402)
        q.delete()
        return Response()


class UsersPipelinesLoadParameterView(APIView):
    def get(self, request, parameter=''):
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
            }
        except KeyError:
            return Response()
        try:
            TaskResult.objects.get(task_id=q.task.task_id).delete()
        except TaskResult.DoesNotExist:
            pass
        q.task = None  # Reset execution
        q.save()
        return Response()


class UsersPipelinesDuplicateView(APIView):
    def post(self, request):
        try:
            pipeline_name = request.data['pipeline_name']
            q = models.Pipeline.objects.get(owner=request.user, name=pipeline_name)
        except models.Pipeline.DoesNotExist:
            return Response(data=f"Pipeline named {pipeline_name} does not exist", status=401)
        except KeyError:
            return Response(data=f"Pipeline name not submitted in the request", status=402)
        new_q = models.Pipeline(name=q.name + "_duplicate", owner=q.owner, parameters=q.parameters, pipeline_type=q.pipeline_type)
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
        q.name = request.data["new_pipeline_name"]
        q.save()
        return Response()


class UsersPipelinesProcessView(APIView):
    def post(self, request):
        """Launch a new pipeline"""
        try:
            pipeline_name = request.data['pipeline_name']
            q = models.Pipeline.objects.get(owner=request.user, name=pipeline_name)
        except models.Pipeline.DoesNotExist:
            return Response(data=f"Pipeline named {pipeline_name} does not exist", status=401)
        except KeyError:
            return Response(data=f"Pipeline name not submitted in the request", status=402)

        # Launch pipeline asyncronously
        location = join(settings.MEDIA_ROOT, q.owner.username, "pipelines")
        makedirs(location, exist_ok=True)
        from .. import celery
        task = celery.launch_pipeline.delay(q.pipeline_type, q.parameters, join(location, q.name))

        # Doesn't work in test, anyway
        try:
            q.task = TaskResult.objects.get(task_id=task.id)
        except TaskResult.DoesNotExist:
            pass
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
        if q.task is None:
            return Response(data=0)
        task_result = TaskResult.objects.get(task_id=q.task.task_id)
        if task_result.status == "SUCCESS":
            return Response(data=3)
        elif task_result.status == "FAILURE":
            return Response(data=2)
        elif task_result.status == "STARTED":
            return Response(data=1)


class UsersPipelinesLogsView(APIView):
    def get(self, request):
        """Get the pipeline state"""
        try:
            pipeline_name = request.query_params['pipeline_name']
            q = models.Pipeline.objects.get(owner=request.user, name=pipeline_name)
        except models.Pipeline.DoesNotExist:
            return Response(data=f"Pipeline named {pipeline_name} does not exist", status=401)
        except KeyError:
            return Response(data=f"Pipeline name not submitted in the request", status=402)
        l = join(settings.MEDIA_ROOT, q.owner.username, "pipelines", q.name, "messages.log")
        with open(l, 'r') as f:
            return Response(f.read())
