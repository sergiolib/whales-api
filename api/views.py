import re
from glob import glob
import json
from os import makedirs, remove
from os.path import join

from rest_framework.response import Response
from rest_framework.views import APIView
from api.getters import GettersData
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from . import getters
from . import models


def convert(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


class GetOptionsView(APIView):
    def get(self, request):
        if request.user.is_anonymous:
            return Response("Must login to be able to upload data files")
        class_name = self.__class__.__name__[:-4]
        class_name = convert(class_name)
        res = GettersData(class_name).to_list()

        # Remove data parameter (user shouldn't see this parameter... shouldn't be here in the first place but meh)
        for r in res:
            if "data" in r['parameters']:
                del r['parameters']["data"]
            if "target" in r['parameters']:
                del r['parameters']["target"]

        return Response(res)


class FormattersView(GetOptionsView):
    pass


class PreProcessingView(GetOptionsView):
    pass


class DataFilesView(GetOptionsView):
    pass


class PipelinesView(GetOptionsView):
    pass


class FeaturesExtractorsView(GetOptionsView):
    pass


class SupervisedMethodsView(GetOptionsView):
    pass


class UnsupervisedMethodsView(GetOptionsView):
    pass


class SemiSupervisedMethodsView(GetOptionsView):
    pass


class PerformanceIndicatorsView(GetOptionsView):
    pass


class StoreView(APIView):
    def post(self, request):
        if request.user.is_anonymous:
            return Response(f"Must login to be able to upload {self.scope} files", status=400)
        file = request.FILES['file']
        user = request.user.username
        location = join(settings.MEDIA_ROOT, user, f"{self.scope}_files")
        return Response(**self.save_file_in_location(file, location))

    def save_file_in_location(self, file, location):
        makedirs(location, exist_ok=True)
        final_location = join(location, file.name)
        final_location = default_storage.save(final_location, ContentFile(file.read()))
        json.dump({"public": False}, open(final_location + ".json", 'w'))
        return {"data": {"message": "Upload successful"}, "status": 200}

    def get(self, request):
        if request.user.is_anonymous:
            return Response("Must login to be able to download data files", status=400)
        res = self.get_private_files(request.user)
        if request.user.can_see_public_files:
            res += self.get_public_files()
        return Response(res)

    def delete(self, request):
        if request.user.is_anonymous:
            return Response(f"Must login to be able to delete {self.scope} files", status=400)
        res = self.get_private_files(request.user)
        data_to_delete = request.data["elements"]
        private_file_names = [i["name"] for i in res]
        for data_file in data_to_delete:
            name = data_file["name"]
            owner = data_file["owner"]
            if name in private_file_names and owner == request.user.username:
                path = join(settings.MEDIA_ROOT, owner, f"{self.scope}_files", name)
                try:
                    remove(path)
                    remove(path + ".json")
                except Exception as e:
                    print(e)
                    return Response(data={"message": e, "status": "Error"}, status=400)
            else:
                print(f"File {name} not found")
                return Response(data={"message": f"File {name} not found", "status": "Error"}, status=400)
        return Response()

    def patch(self, request):
        if request.user.is_anonymous:
            return Response(f"Must login to be able to delete {self.scope} files", status=400)
        res = self.get_private_files(request.user) + self.get_public_files()
        data_to_patch = request.data["elements"]
        operation = request.data.get("operation")

        if operation == "toggle_public":
            file_names = [i["name"] for i in res]
            for data_file in data_to_patch:
                name = data_file["name"]
                owner = data_file["owner"]
                public = data_file["public"]
                if name in file_names and owner == request.user.username:
                    path = join(settings.MEDIA_ROOT, owner, f"{self.scope}_files", name)
                    try:
                        d = json.load(open(path + ".json", 'r'))
                        d['public'] = not public
                        json.dump(d, open(path + ".json", 'w'))
                    except Exception as e:
                        print(e)
                        return Response(data={"message": e, "status": "Error"}, status=400)
                else:
                    print(f"File {name} not found")
                    return Response(data={"message": f"File {name} not found", "status": "Error"}, status=400)
        return Response()

    def get_public_files(self):
        all_datafiles = glob(join(settings.MEDIA_ROOT, '*', f"{self.scope}_files", f"*.{self.file_format}"))
        is_public = {}
        res = []
        for f in all_datafiles:
            meta = json.load(open(f + ".json", 'r'))
            is_public[f] = meta["public"]
        for f in all_datafiles:
            if is_public[f]:
                owner, _, name = f.split("/")[-3:]
                res.append({"name": name, "owner": owner, "public": True})
        return res

    def get_private_files(self, user):
        all_datafiles = glob(join(settings.MEDIA_ROOT, user.get_username(), f"{self.scope}_files", f"*.{self.file_format}"))
        res = []
        is_public = {}
        for f in all_datafiles:
            meta = json.load(open(f + ".json", 'r'))
            is_public[f] = meta["public"]
        for f in all_datafiles:
            if not is_public[f]:
                owner, _, name = f.split("/")[-3:]
                res.append({"name": name, "owner": owner, "public": False})
        return res


class DataView(StoreView):
    scope = "data"
    file_format = "aif"
        

class LabelsView(StoreView):
    scope = "labels"
    file_format = "csv"


class UsersPipelinesView(APIView):
    def get(self, request):
        if request.user.is_anonymous:
            return Response(f"Must login to be able to see the user's pipelines", status=400)
        q = models.Pipeline.objects.filter(owner=request.user)
        q = [{'name': i.name, 'parameters': i.parameters, 'type': i.pipeline_type} for i in q]
        return Response(data=q)

    def post(self, request):
        if "new_pipeline_name" in request.data:
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

        else:
            # Save pipeline to db
            try:
                q = models.Pipeline.objects.get(owner=request.user, name=request.data["pipeline_name"])
            except models.Pipeline.DoesNotExist:
                return Response(data=f"Pipeline named {request.data['pipeline_name']} does not exist", status=401)
            except KeyError:
                return Response(data=f"Pipeline name not submitted in the request", status=402)
            q.parameters = request.data['parameters']
            q.save()

        return Response(data="ok")

    def delete(self, request):
        try:
            q = models.Pipeline.objects.get(owner=request.user, name=request.data["pipeline_name"])
        except models.Pipeline.DoesNotExist:
            return Response(data=f"Pipeline named {request.data['pipeline_name']} does not exist", status=401)
        except KeyError:
            return Response(data=f"Pipeline name not submitted in the request", status=402)
        q.delete()
        return Response()


class UsersPipelinesDuplicateView(APIView):
    def post(self, request):
        try:
            q = models.Pipeline.objects.get(owner=request.user, name=request.data["pipeline_name"])
        except models.Pipeline.DoesNotExist:
            return Response(data=f"Pipeline named {request.data['pipeline_name']} does not exist", status=401)
        except KeyError:
            return Response(data=f"Pipeline name not submitted in the request", status=402)
        new_q = models.Pipeline(name=q.name + "_duplicate", owner=q.owner, parameters=q.parameters, pipeline_type=q.pipeline_type)
        new_q.save()
        return Response()


class UsersPipelinesRenameView(APIView):
    def post(self, request):
        try:
            q = models.Pipeline.objects.get(owner=request.user, name=request.data["pipeline_name"])
        except models.Pipeline.DoesNotExist:
            return Response(data=f"Pipeline named {request.data['pipeline_name']} does not exist", status=401)
        except KeyError:
            return Response(data=f"Pipeline name not submitted in the request", status=402)
        q.name = request.data["new_pipeline_name"]
        q.save()
        return Response()
