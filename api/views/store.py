from os import makedirs, remove
from os.path import join

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from rest_framework.response import Response
from rest_framework.views import APIView
from api import models


class GetStoreView(APIView):
    def get(self, request):
        if request.user.is_anonymous:
            return Response("Must login to be able to download data files", status=400)
        res = self.get_private_files(request.user)
        if request.user.can_see_public_files:
            res += self.get_public_files()
        return Response(res)

    def get_private_files(self, user):
        pass

    def get_public_files(self):
        pass


class GetLabelsView(GetStoreView):
    def get_public_files(self):
        files = models.LabelsFile.objects.filter(public=True).values()
        return list(files)

    def get_private_files(self, user):
        files = models.LabelsFile.objects.filter(public=False, owner=user).values()
        return list(files)


class GetDataView(GetStoreView):
    def get_public_files(self):
        files = models.DataFile.objects.filter(public=True).values()
        return list(files)

    def get_private_files(self, user):
        files = models.DataFile.objects.filter(public=False, owner=user).values()
        return list(files)


class StoreView(APIView):
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
                    return Response(data={"message": e, "status": "Error"}, status=400)
            else:
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
                        return Response(data={"message": e, "status": "Error"}, status=400)
                else:
                    return Response(data={"message": f"File {name} not found", "status": "Error"}, status=400)
        return Response()


class StoreDataView(StoreView):
    def put(self, request, data_file, formatter):
        if request.user.is_anonymous:
            return Response(f"Must login to be able to upload files", status=400)
        file = request.FILES['file']
        return self.save_file_in_location(file, owner=request.user, data_file=data_file, formatter=formatter)

    def save_file_in_location(self, file, owner, data_file, formatter):
        location = join(settings.MEDIA_ROOT, owner.username, "data_files")
        makedirs(location, exist_ok=True)
        final_location = join(location, file.name)
        final_location = default_storage.save(final_location, ContentFile(file.read()))
        models.DataFile(location=final_location, owner=owner, data_file=data_file, formatter=formatter).save()
        return Response()


class StoreLabelsView(StoreView):
    def put(self, request, formatter):
        if request.user.is_anonymous:
            return Response(f"Must login to be able to upload files", status=400)
        file = request.FILES['file']
        return self.save_file_in_location(file, owner=request.user, formatter=formatter)

    def save_file_in_location(self, file, owner, formatter):
        location = join(settings.MEDIA_ROOT, owner.username, "labels_files")
        makedirs(location, exist_ok=True)
        final_location = join(location, file.name)
        final_location = default_storage.save(final_location, ContentFile(file.read()))
        models.LabelsFile(location=final_location, owner=owner, formatter=formatter).save()
        return Response()
