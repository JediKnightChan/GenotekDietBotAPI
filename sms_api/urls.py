from django.urls import path

from . import views

urlpatterns = [
    path('create_verification_code/', views.create_verification_code, name='create_verification_code'),
    path('check_verification_code/', views.check_verification_code, name='check_verification_code'),
    path('need_phone_verification/', views.need_phone_verification, name='need_phone_verification'),
]
