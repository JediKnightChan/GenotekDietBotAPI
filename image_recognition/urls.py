from django.urls import path, include
from . import views


urlpatterns = [
    path('recognise/', views.recognise_image, name='recognise_image'),
]
