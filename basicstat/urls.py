from django.urls import include, path

from . import views

urlpatterns = [
    path('bmi/', views.body_mass_index, name='body_mass_index'),
]
