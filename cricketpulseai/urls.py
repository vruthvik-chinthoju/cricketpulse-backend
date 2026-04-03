from django.urls import path
from .views import predict_api

urlpatterns = [
    path("predictmatch/", predict_api),
]