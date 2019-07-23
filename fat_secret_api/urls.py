from django.urls import path
from . import views


urlpatterns = [
    path('get_auth_url/', views.get_auth_url, name='get_auth_url'),
    path('auth/', views.authenticate, name='authenticate'),
    path('create_bot_user/', views.create_bot_user, name='create_bot_user'),
    path('create_fatsecret_profile/', views.create_fatsecret_profile, name='create_fatsecret_profile'),
    path('need_fatsecret_account/', views.need_fatsecret_account, name='need_fatsecret_account'),
    path('auth_check_success/', views.authenticate_check_success, name='authenticate_check_success')
]
