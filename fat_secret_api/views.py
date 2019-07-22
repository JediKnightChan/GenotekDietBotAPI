from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, reverse

from django.conf import settings
from fatsecret import Fatsecret
from requests.compat import urljoin
from .models import BotUser


@csrf_exempt
def create_bot_user(request):
    if request.POST['token'] == settings.BOTMOTHER_TOKEN:
        user_id = request.POST['user_id']
        user = BotUser.objects.create(bot_user_id=user_id)
        user.save()


@csrf_exempt
def create_fatsecret_profile(request):
    fs = Fatsecret(settings.CONSUMER_KEY, settings.CONSUMER_SECRET)
    if request.POST['token'] == settings.BOTMOTHER_TOKEN:
        session_token = fs.profile_create('new_user_001')
        user_id = request.POST['user_id']

        user = BotUser.objects.get(bot_user_id=user_id)
        user.fatsecret_oauth_token = session_token[0]
        user.fatsecret_oauth_token_secret = session_token[1]
        user.save()


@csrf_exempt
def get_auth_url(request):
    if request.POST['token'] == settings.BOTMOTHER_TOKEN:
        fs = Fatsecret(settings.CONSUMER_KEY, settings.CONSUMER_SECRET)
        user_id = request.POST['user_id']
        callback_url = urljoin(settings.REDIRECT_HOST, reverse('authenticate'))
        callback_url = urljoin(callback_url, '?user_id={}'.format(user_id))
        auth_url = fs.get_authorize_url(callback_url=callback_url)
        return JsonResponse({"url": auth_url})


def authenticate(request):
    fs = Fatsecret(settings.CONSUMER_KEY, settings.CONSUMER_SECRET)
    if request.args.get('oauth_verifier'):
        user_id = int(request.GET['user_id'])
        verifier_pin = request.args.get('oauth_verifier')
        session_token = fs.authenticate(verifier_pin)
        print(user_id, "token is", session_token)
        return render(request, "fat_secret_api/auth_complete.html")
    else:
        return JsonResponse({"error": "Authentication cannot be completed"})
