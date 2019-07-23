from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, reverse
from django.conf import settings

from fatsecret import Fatsecret
from fatsecret.fatsecret import ParameterError as FSParameterError

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
        user = BotUser.objects.create(bot_user_id=user_id, fatsecret_account='NO')
        user.save()
    return JsonResponse({"success": True})


@csrf_exempt
@api_safe_run(logger, token_required=True)
def create_fatsecret_profile(request):
    fs = Fatsecret(settings.CONSUMER_KEY, settings.CONSUMER_SECRET)
    user_id = request.POST['user_id']
    if BotUser.objects.filter(bot_user_id=user_id).first() is None:
        return JsonResponse({"success": False, "error": "User with this id doesn't exist"})
    elif BotUser.objects.get(bot_user_id=user_id).fatsecret_account != "NO":
        return JsonResponse({"success": False, "error": "User with this id already has a FS account"})

    try:
        session_token = fs.profile_create(str(user_id))
    except FSParameterError:
        # This user already has a new FS account
        session_token = fs.profile_get_auth(str(user_id))

    user = BotUser.objects.get(bot_user_id=user_id)
    user.fatsecret_account = 'NEW'
    user.fatsecret_oauth_token = session_token[0]
    user.fatsecret_oauth_token_secret = session_token[1]
    user.save()
    return JsonResponse({"success": True})


@csrf_exempt
@api_safe_run(logger, token_required=True)
def need_fatsecret_account(request):
    user_id = request.POST['user_id']
    if BotUser.objects.filter(bot_user_id=user_id).first() is None:
        return JsonResponse({"success": False, "error": "User with this id doesn't exist"})
    elif BotUser.objects.filter(bot_user_id=user_id).first() == "NO":
        return JsonResponse({"success": True, "need": True})
    else:
        return JsonResponse({"success": True, "need": False})


@csrf_exempt
@api_safe_run(logger, token_required=True)
def get_auth_url(request):
    fs = Fatsecret(settings.CONSUMER_KEY, settings.CONSUMER_SECRET)
    user_id = request.POST['user_id']
    if BotUser.objects.filter(bot_user_id=user_id).first() is None:
        return JsonResponse({"success": False, "error": "User with this id doesn't exist"})
    elif BotUser.objects.get(bot_user_id=user_id).fatsecret_account != "NO":
        return JsonResponse({"success": False, "error": "User with this id already has a FS account"})

    callback_url = urljoin(settings.REDIRECT_HOST, reverse('authenticate'))
    callback_url = urljoin(callback_url, '?user_id={}'.format(user_id))
    auth_url = fs.get_authorize_url(callback_url=callback_url)

    # Saving request token and secret for further fs instance creation in 'authenticate'
    user = BotUser.objects.get(bot_user_id=user_id)
    user.fs_request_token = fs.request_token
    user.fs_request_token_secret = fs.request_token_secret
    user.save()

    return JsonResponse({"success": True, "url": auth_url})


@api_safe_run(logger)
def authenticate(request):
    fs = Fatsecret(settings.CONSUMER_KEY, settings.CONSUMER_SECRET)
    if request.GET.get('oauth_verifier', None):
        user_id = int(request.GET['user_id'])
        verifier_pin = request.GET['oauth_verifier']

        # Changing fs to use variables from 1st step of 3-Legged OAuth
        user = BotUser.objects.get(bot_user_id=user_id)
        fs.request_token = user.fs_request_token
        fs.request_token_secret = user.fs_request_token_secret

        session_token = fs.authenticate(verifier_pin)
        logger.info("Successful authentication. Token is {}, user id is {}".format(session_token, user_id))

        user.fatsecret_account = 'OLD'
        user.fatsecret_oauth_token = session_token[0]
        user.fatsecret_oauth_token_secret = session_token[1]
        user.save()

        return render(request, "fat_secret_api/auth_complete.html")
    else:
        return JsonResponse({"error": "Authentication cannot be completed: OAUTH verifier is not set"})


@csrf_exempt
@api_safe_run(logger, token_required=True)
def authenticate_check_success(request):
    user_id = int(request.GET['user_id'])
    if BotUser.objects.filter(bot_user_id=user_id).first() is None:
        return JsonResponse({"success": False, "error": "User with this id doesn't exist"})
    elif BotUser.objects.filter(bot_user_id=user_id).first() == "OLD":
        return JsonResponse({"success": True, "auth_success": True})
    else:
        return JsonResponse({"success": True, "auth_success": False})
