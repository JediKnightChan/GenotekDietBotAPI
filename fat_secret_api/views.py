from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, reverse
from django.conf import settings
from django.utils.timezone import now, pytz

from fatsecret import Fatsecret
from fatsecret.fatsecret import ParameterError as FSParameterError
import requests
from requests.compat import urljoin
import logging
import json

from generic.additional import api_safe_run
from .additional import hour_to_meal
from .models import BotUser

logger = logging.getLogger(__name__)

food_recognition_url = 'https://api.clarifai.com/v2/models/bd367be194cf45149e75f01d59f77ba7/outputs'
food_recognition_headers = {
    "Content-Type": "application/json",
    "Authorization": "Key {}".format(settings.FOOD_RECOGNITION_API_KEY),
}


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
    elif BotUser.objects.get(bot_user_id=user_id).fatsecret_account == "NO":
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
    user_id = int(request.POST['user_id'])
    if BotUser.objects.filter(bot_user_id=user_id).first() is None:
        return JsonResponse({"success": False, "error": "User with this id doesn't exist"})
    elif BotUser.objects.get(bot_user_id=user_id).fatsecret_account == "OLD":
        return JsonResponse({"success": True, "auth_success": True})
    else:
        return JsonResponse({"success": True, "auth_success": False})


@csrf_exempt
@api_safe_run(logger, token_required=True)
def get_calories_today(request):
    user_id = int(request.POST['user_id'])
    if BotUser.objects.filter(bot_user_id=user_id).first() is None:
        return JsonResponse({"success": False, "error": "User with this id doesn't exist"})
    elif BotUser.objects.get(bot_user_id=user_id).fatsecret_account == "NO":
        return JsonResponse({"success": False, "error": "User not authorized"})

    user = BotUser.objects.get(bot_user_id=user_id)
    session_token = user.fatsecret_oauth_token, user.fatsecret_oauth_token_secret
    fs = Fatsecret(settings.CONSUMER_KEY, settings.CONSUMER_SECRET, session_token=session_token)
    dt = now().astimezone(pytz.timezone(settings.TIME_ZONE)).replace(tzinfo=None)

    with open("recommended.json") as f:
        calories_rec = json.load(f)["calories"]
    recent_eaten = fs.food_entries_get(date=dt)
    if not recent_eaten:
        return JsonResponse({"success": True, "message": "Похоже, сегодня вы ничего не добавляли в наш помощник."})

    calories_eaten = []
    for food_item in recent_eaten:
        calories_eaten.append(int(food_item['calories']))
    calories_eaten = sum(calories_eaten)
    if calories_eaten > calories_rec:
        return JsonResponse({"success": True, "message": "Похоже, сегодня вы съели слишком много калорий."})
    else:
        return JsonResponse({"success": True, "message": "Сегодня вы съели не слишком много калорий."})


@csrf_exempt
@api_safe_run(logger, token_required=True)
def recognise_image(request):
    image_url = request.POST['image_url']
    user_id = int(request.POST['user_id'])
    if BotUser.objects.filter(bot_user_id=user_id).first() is None:
        return JsonResponse({"success": False, "error": "User with this id doesn't exist"})
    elif BotUser.objects.get(bot_user_id=user_id).fatsecret_account == "NO":
        return JsonResponse({"success": False, "error": "User not authorized"})

    api_request_body = {
        "inputs": [
            {
                "data": {
                    "image": {
                        "url": image_url
                    }
                }
            }
        ]
    }
    r = requests.post(food_recognition_url, data=json.dumps(api_request_body), headers=food_recognition_headers)
    response_body = r.json()
    possible_products = list(filter(lambda p: p["value"] > 0.8, response_body["outputs"][0]["data"]["concepts"]))[:4]
    possible_products = " ".join(map(lambda p: p["name"], possible_products))

    user = BotUser.objects.get(bot_user_id=user_id)
    session_token = user.fatsecret_oauth_token, user.fatsecret_oauth_token_secret
    fs = Fatsecret(settings.CONSUMER_KEY, settings.CONSUMER_SECRET, session_token=session_token)

    food_names = []
    food_ids = []
    for food_item in fs.foods_search(possible_products)[:4]:
        food_names.append(food_item["food_name"])
        food_ids.append(food_item["food_id"])
    return JsonResponse({"success": True, "food_names": food_names, "food_ids": food_ids})


@csrf_exempt
@api_safe_run(logger, token_required=True)
def get_serving_for_food_id(request):
    food_id = str(request.POST['food_id'])
    fs = Fatsecret(settings.CONSUMER_KEY, settings.CONSUMER_SECRET)
    needed_serving = fs.food_get(food_id)["servings"]["serving"][-1]
    measure = needed_serving["measurement_description"]
    serving_id = needed_serving["serving_id"]
    return JsonResponse({"success": True, "measure": measure, "serving_id": serving_id})


@csrf_exempt
@api_safe_run(logger, token_required=True)
def create_food_entry(request):
    user_id = int(request.POST['user_id'])
    food_id = str(request.POST['food_id'])
    serving_id = str(request.POST['serving_id'])
    number_of_units = float(request.POST['number_of_units'])

    if BotUser.objects.filter(bot_user_id=user_id).first() is None:
        return JsonResponse({"success": False, "error": "User with this id doesn't exist"})
    elif BotUser.objects.get(bot_user_id=user_id).fatsecret_account == "NO":
        return JsonResponse({"success": False, "error": "User not authorized"})

    user = BotUser.objects.get(bot_user_id=user_id)
    session_token = user.fatsecret_oauth_token, user.fatsecret_oauth_token_secret
    fs = Fatsecret(settings.CONSUMER_KEY, settings.CONSUMER_SECRET, session_token=session_token)
    dt = now().astimezone(pytz.timezone(settings.TIME_ZONE)).replace(tzinfo=None)
    meal = hour_to_meal(dt.hour)
    entry_name = "{}: {}".format(dt.ctime(), fs.food_get(food_id)['food_name'])
    fs.food_entry_create(food_id, entry_name, serving_id, number_of_units, meal)
    return JsonResponse({"success": True})
