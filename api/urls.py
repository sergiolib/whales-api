from django.urls import include, path
from . import views

urlpatterns = [
    path('store/input_data/<str:data_file>/<str:formatter>', views.StoreDataView.as_view(), name="store_data_files"),
    path('get/input_data', views.GetDataView.as_view(), name="get_data_files"),
    path('store/input_labels/<str:formatter>', views.StoreLabelsView.as_view(), name="store_labels_files"),
    path('get/input_labels', views.GetLabelsView.as_view(), name="get_labels_files"),
    path('get/<str:scope>', views.GetScopeOptionsView.as_view()),
    path('user_pipelines', views.UsersPipelinesView.as_view()),
    path('user_pipelines/create', views.UsersPipelinesCreateView.as_view()),
    path('user_pipelines/delete', views.UsersPipelinesDeleteView.as_view()),
    path('user_pipelines/logs', views.UsersPipelinesLogsView.as_view()),
    path('user_pipelines/results', views.UsersPipelinesResultsView.as_view()),
    path('user_pipelines/save/<str:parameter>', views.UsersPipelinesSaveParameterView.as_view()),
    path('user_pipelines/load/<str:parameter>', views.UsersPipelinesLoadParameterView.as_view()),
    path('user_pipelines/process', views.UsersPipelinesProcessView.as_view()),
    path('user_pipelines/duplicate', views.UsersPipelinesDuplicateView.as_view()),
    path('user_pipelines/rename', views.UsersPipelinesRenameView.as_view()),
]
