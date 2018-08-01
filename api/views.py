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


def convert(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


class GetOptionsView(APIView):
    def get(self, request):
        if request.user.is_anonymous:
            return Response("Must login to be able to upload data files")
        class_name = self.__class__.__name__[:-4]
        class_name = convert(class_name)
        return Response(GettersData(class_name).to_list())


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
