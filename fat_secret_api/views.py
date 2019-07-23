from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, reverse
from django.conf import settings

from fatsecret import Fatsecret
from requests.compat import urljoin
import logging

from generic.additional import api_safe_run
from .models import BotUser

logger = logging.getLogger(__name__)


@csrf_exempt
@api_safe_run(logger, token_required=True)
def create_bot_user(request):
    user_id = request.POST['user_id']
    if BotUser.objects.filter(bot_user_id=user_id).first() is None:
        user = BotUser.objects.create(bot_user_id=user_id)
        user.save()
    return JsonResponse({"success": True})


@csrf_exempt
@api_safe_run(logger, token_required=True)
def create_fatsecret_profile(request):
    fs = Fatsecret(settings.CONSUMER_KEY, settings.CONSUMER_SECRET)
    session_token = fs.profile_create('new_user_001')
    user_id = request.POST['user_id']

    user = BotUser.objects.get(bot_user_id=user_id)
    user.fatsecret_oauth_token = session_token[0]
    user.fatsecret_oauth_token_secret = session_token[1]
    user.save()
    return JsonResponse({"success": True})


@csrf_exempt
@api_safe_run(logger, token_required=True)
def get_auth_url(request):
    fs = Fatsecret(settings.CONSUMER_KEY, settings.CONSUMER_SECRET)
    user_id = request.POST['user_id']
    callback_url = urljoin(settings.REDIRECT_HOST, reverse('authenticate'))
    callback_url = urljoin(callback_url, '?user_id={}'.format(user_id))
    auth_url = fs.get_authorize_url(callback_url=callback_url)
    return JsonResponse({"url": auth_url, "success": True})


@api_safe_run(logger)
def authenticate(request):
    fs = Fatsecret(settings.CONSUMER_KEY, settings.CONSUMER_SECRET)
    if request.args.get('oauth_verifier'):
        user_id = int(request.GET['user_id'])
        verifier_pin = request.args.get('oauth_verifier')
        session_token = fs.authenticate(verifier_pin)
        logger.info("Successful authentication. Token is {}, user id is {}".format(session_token, user_id))

        user = BotUser.objects.get(bot_user_id=user_id)
        user.fatsecret_oauth_token = session_token[0]
        user.fatsecret_oauth_token_secret = session_token[1]
        user.save()

        return render(request, "fat_secret_api/auth_complete.html")
    else:
        return JsonResponse({"error": "Authentication cannot be completed: OAUTH verifier is not set"})
