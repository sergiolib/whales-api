from django.urls import include, path
from . import views

urlpatterns = [
    path('formatters/', views.FormattersView.as_view()),
    path('pre_processing/', views.PreProcessingView.as_view()),
    path('data_files_types/', views.DataFilesView.as_view()),
    path('pipelines/', views.PipelinesView.as_view()),
    path('features_extractors/', views.FeaturesExtractorsView.as_view()),
    path('supervised_methods/', views.SupervisedMethodsView.as_view()),
    path('unsupervised_methods/', views.UnsupervisedMethodsView.as_view()),
    path('semi_supervised_methods/', views.SemiSupervisedMethodsView.as_view()),
    path('performance_indicators/', views.PerformanceIndicatorsView.as_view()),
    path('data_files/', views.DataView.as_view()),
    path('labels_files/', views.LabelsView.as_view()),
]
