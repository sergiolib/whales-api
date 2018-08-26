import random
import sys
from django.conf import settings
sys.path.append(settings.WHALES_BACKEND)

from whales.utilities.testing import get_labeled
from os import makedirs
from os.path import join, dirname

from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.reverse import reverse
from rest_framework.test import force_authenticate, APIRequestFactory, APIClient
from django.test import TestCase
from api.models import User, Pipeline
from api.views import UsersPipelinesLoadParameterView, UsersPipelinesSaveParameterView, \
    GetScopeOptionsView, UsersPipelinesCreateView, UsersPipelinesView, \
    UsersPipelinesDuplicateView, UsersPipelinesRenameView, UsersPipelinesLogsView, \
    UsersPipelinesDeleteView, UsersPipelinesProcessView


class WhalesAPI(TestCase):
    def setUp(self):
        test_user = User(
            username="test"
        )
        test_user.save()
        Pipeline(
            name="test",
            owner=test_user,
            pipeline_type="Predictions pipeline",
            parameters={}
        ).save()

    def test_get_parameters(self):
        scopes_default_values = {k: v['value'] for k, v in Pipeline.objects.all()[0].parameters.items()}
        for scope in scopes_default_values.keys():
            factory = APIRequestFactory()
            user = User.objects.get(username='test')
            view = UsersPipelinesLoadParameterView.as_view()
            request = factory.get('?pipeline_name=test', format="json")
            force_authenticate(request, user=user)
            response = view(request, scope)
            v = response.data["value"]
            t = scopes_default_values[scope]
            self.assertEqual(v, t)

    def test_update_machine_learning_parameters(self):
        scopes_default_values = {k: v['value'] for k, v in Pipeline.objects.all()[0].parameters.items()}
        scopes_demo_values = {
            'machine_learning': {
                "type": "supervised",
                "value": {
                    "method": "svm",
                    "parameters": {}
                },
            },
            'pre_processing': {
                "value": {
                    "method": "sliding_windows",
                    "parameters": {}
                },
            },
            'features_extractors': {
                "value": {
                    "method": "skewness",
                    "parameters": {}
                },
            },
            'performance_indicators': {
                "value": {
                    "method": "accuracy",
                    "parameters": {}
                },
            },
            'input_data': {
                "value": [
                    {
                        "file_name": "hello",
                        "data_file": "audio",
                        "formatter": "aif",
                    }
                ],
            },
            'input_labels': {
                "value": [
                    {
                        "labels_file": "hello",
                        "labels_formatter": "csv",
                    }
                ],
            },
            'verbose': {
                "value": True
            }
        }
        for scope in scopes_default_values.keys():
            factory = APIRequestFactory()
            user = User.objects.get(username='test')
            view = UsersPipelinesSaveParameterView.as_view()
            request = factory.post('?pipeline_name=test', data=scopes_demo_values[scope], format="json")
            force_authenticate(request, user=user)
            response = view(request, scope)

            factory = APIRequestFactory()
            user = User.objects.get(username='test')
            view = UsersPipelinesLoadParameterView.as_view()
            request = factory.get('?pipeline_name=test', format="json")
            force_authenticate(request, user=user)
            response = view(request, scope)

            self.assertEqual(response.data["value"], scopes_demo_values[scope]["value"])

    def test_get_options(self):
        scopes = [k for k in Pipeline.objects.all()[0].parameters]
        all_data = []
        for scope in scopes:
            factory = APIRequestFactory()
            user = User.objects.get(username='test')
            view = GetScopeOptionsView.as_view()
            request = factory.get('?pipeline_name=test', format="json")
            force_authenticate(request, user=user)
            response = view(request, scope)
            all_data.append(response.data)

    def test_create_new_pipeline(self):
        factory = APIRequestFactory()
        user = User.objects.get(username='test')
        view = UsersPipelinesCreateView.as_view()
        request = factory.post('',
                               data={
                                   "new_pipeline_name": "test2",
                                   "new_pipeline_type": "Training pipeline"
                               },
                               format="json")
        force_authenticate(request, user=user)
        response = view(request)

        factory = APIRequestFactory()
        view = UsersPipelinesView.as_view()
        request = factory.get('', format="json")
        force_authenticate(request, user=user)
        response = view(request)

        is_in = False
        for i in response.data:
            if i['name'] == "test2":
                is_in = True

        assert is_in

        factory = APIRequestFactory()
        view = UsersPipelinesDeleteView.as_view()
        request = factory.delete('?pipeline_name=test2', format="json")
        force_authenticate(request, user=user)
        response = view(request)

    def test_duplicate_pipeline(self):
        factory = APIRequestFactory()
        user = User.objects.get(username='test')
        view = UsersPipelinesDuplicateView.as_view()
        request = factory.post('',
                               data={
                                   "pipeline_name": "test",
                               },
                               format="json")
        force_authenticate(request, user=user)
        response = view(request)

        factory = APIRequestFactory()
        view = UsersPipelinesView.as_view()
        request = factory.get('', format="json")
        force_authenticate(request, user=user)
        response = view(request)

        is_in = False
        for i in response.data:
            if i['name'] == "test_duplicate":
                is_in = True

        assert is_in

    def test_rename_pipeline(self):
        factory = APIRequestFactory()
        user = User.objects.get(username='test')
        view = UsersPipelinesRenameView.as_view()
        request = factory.post('',
                               data={
                                   "pipeline_name": "test",
                                   "new_pipeline_name": "test3"
                               },
                               format="json")
        force_authenticate(request, user=user)
        response = view(request)

        factory = APIRequestFactory()
        view = UsersPipelinesView.as_view()
        request = factory.get('', format="json")
        force_authenticate(request, user=user)
        response = view(request)

        is_in = False
        for i in response.data:
            if i['name'] == "test3":
                is_in = True

        assert is_in

        factory = APIRequestFactory()
        user = User.objects.get(username='test')
        view = UsersPipelinesRenameView.as_view()
        request = factory.post('',
                               data={
                                   "pipeline_name": "test3",
                                   "new_pipeline_name": "test"
                               },
                               format="json")
        force_authenticate(request, user=user)
        response = view(request)

    def test_logs_of_pipelines(self):
        num = random.randint(0, 10000)
        messages_loc = join(settings.MEDIA_ROOT, "test", "pipelines", "test", "messages.log")

        makedirs(dirname(messages_loc), exist_ok=True)
        with open(messages_loc, 'w') as f:
            f.write(f"{num}")

        factory = APIRequestFactory()
        user = User.objects.get(username='test')
        view = UsersPipelinesLogsView.as_view()
        request = factory.get('?pipeline_name=test',
                              format="json")
        force_authenticate(request, user=user)
        response = view(request)

        assert response.data == f"{num}"

    def test_upload_data_file(self):
        client = APIClient()
        user = User.objects.get(username='test')
        client.force_authenticate(user=user)
        store_url = reverse("store_data_files", kwargs={"data_file": "audio",
                                                        "formatter": "aif"})
        get_url = reverse("get_data_files")
        client.put(store_url,
                   {'file': SimpleUploadedFile(name="hello", content=b"1234")})
        response = client.get(get_url)

    def test_upload_labels_file(self):
        client = APIClient()
        user = User.objects.get(username='test')
        client.force_authenticate(user=user)
        store_url = reverse("store_labels_files", kwargs={"formatter": "csv"})
        get_url = reverse("get_labels_files")
        client.put(store_url,
                   {'file': SimpleUploadedFile(name="hello", content=b"1234")})
        response = client.get(get_url)

    # def test_launch_pipeline(self):
    #     factory = APIRequestFactory()
    #     user = User.objects.get(username='test')
    #     view = UsersPipelinesProcessView.as_view()
    #     labeled = get_labeled()
    #     p = Pipeline(
    #         name="real_working_pipeline",
    #         parameters={
    #             "machine_learning": {
    #                 "method": "svm",
    #                 "type": "supervised",
    #             },
    #             "input_data": [
    #                 {
    #                     "file_name": labeled[0],
    #                     "data_file": "audio",
    #                     "formatter": "aif",
    #                 }
    #             ],
    #             "input_labels": [
    #                 {
    #                     "labels_file": labeled[1],
    #                     "labels_formatter": "csv",
    #                 }
    #             ],
    #             "features_extractors": [
    #                 {
    #                     "method": "mfcc"
    #                 }
    #             ],
    #             "pre_processing": [
    #                 {
    #                     "method": "sliding_windows"
    #                 }
    #             ],
    #         },
    #         pipeline_type="Training pipeline",
    #         owner=user,
    #     )
    #     p.save()
    #     request = factory.post('',
    #                            data={
    #                                "pipeline_name": "real_working_pipeline",
    #                            },
    #                            format="json")
    #     force_authenticate(request, user=user)
    #     response = view(request)
    #
    #     factory = APIRequestFactory()
    #     request = factory.get('?pipeline_name=real_working_pipeline',
    #                           format="json")
    #     force_authenticate(request, user=user)
    #     response = view(request)
    #     pass