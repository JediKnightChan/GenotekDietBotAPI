import json
import logging

import requests
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render, reverse
from django.utils.timezone import now, pytz
from django.views.decorators.csrf import csrf_exempt
from fatsecret import Fatsecret
from fatsecret.fatsecret import ParameterError as FSParameterError
from requests.compat import urljoin

from generic.additional import api_safe_run
from generic.models import BotUser

from .additional import food_search, hour_to_meal

logger = logging.getLogger(__name__)

food_recognition_url = 'https://api.clarifai.com/v2/models/bd367be194cf45149e75f01d59f77ba7/outputs'
food_recognition_headers = {
    "Content-Type": "application/json",
    "Authorization": "Key {}".format(settings.FOOD_RECOGNITION_API_KEY),
}


@csrf_exempt
@api_safe_run(logger, token_required=True)
def create_bot_user(request):
    """ Creates BotUser model instance for the specified platform_id.

    :request_field integer user_id: BotMother user's platform_id.

    :response_field boolean success
    """

    user_id = request.POST['user_id']

    # If user doesn't exist, create user
    if BotUser.objects.filter(bot_user_id=user_id).first() is None:
        user = BotUser.objects.create(bot_user_id=user_id, fatsecret_account='NO')
        user.save()

    return JsonResponse({"success": True})


@csrf_exempt
@api_safe_run(logger, token_required=True)
def create_fatsecret_profile(request):
    """ Creates new FatSecret profile in this FS app for the specified user.

    :response_field boolean success
    """

    fs = Fatsecret(settings.CONSUMER_KEY, settings.CONSUMER_SECRET)
    user_id = request.POST['user_id']

    if BotUser.objects.filter(bot_user_id=user_id).first() is None:
        return JsonResponse({"success": False, "error": "User with this id doesn't exist"})

    try:
        session_token = fs.profile_create(str(user_id))
    except FSParameterError:
        # This user already has a new FS account
        session_token = fs.profile_get_auth(str(user_id))

    # Update user fields
    user = BotUser.objects.get(bot_user_id=user_id)
    user.fatsecret_account = 'NEW'
    user.fatsecret_oauth_token = session_token[0]
    user.fatsecret_oauth_token_secret = session_token[1]
    user.save()

    return JsonResponse({"success": True})


@csrf_exempt
@api_safe_run(logger, token_required=True)
def need_fatsecret_account(request):
    """ Answers whether the bot user already has FS profile in this app.

    :request_field integer user_id: BotMother user's platform_id.

    :response_field boolean need: Whether user needs a FS profile.
    :response_field boolean success
    """

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
    """ Requests url for an existing FS account binding to the specified user.

    :response_field string url: FS account binding URL.
    :response_field boolean success
    """

    fs = Fatsecret(settings.CONSUMER_KEY, settings.CONSUMER_SECRET)
    user_id = request.POST['user_id']
    if BotUser.objects.filter(bot_user_id=user_id).first() is None:
        return JsonResponse({"success": False, "error": "User with this id doesn't exist"})

    # Creating auth_url where token contains callback_url to our server page
    callback_url = urljoin(settings.REDIRECT_HOST, reverse('authenticate'))
    callback_url = urljoin(callback_url, '?user_id={}'.format(user_id))
    auth_url = fs.get_authorize_url(callback_url=callback_url)

    # Saving request token and secret for further FS instance creation in 'authenticate'
    user = BotUser.objects.get(bot_user_id=user_id)
    user.fs_request_token = fs.request_token
    user.fs_request_token_secret = fs.request_token_secret
    user.save()

    return JsonResponse({"success": True, "url": auth_url})


@api_safe_run(logger)
def authenticate(request):
    """ Page where user is redirected from a FS account binding confirmation page to complete FS account binding.
    """

    fs = Fatsecret(settings.CONSUMER_KEY, settings.CONSUMER_SECRET)
    if request.GET.get('oauth_verifier', None):
        user_id = int(request.GET['user_id'])
        verifier_pin = request.GET['oauth_verifier']

        # Changing FS instance to use variables from 1st step of 3-Legged OAuth
        user = BotUser.objects.get(bot_user_id=user_id)
        fs.request_token = user.fs_request_token
        fs.request_token_secret = user.fs_request_token_secret

        session_token = fs.authenticate(verifier_pin)
        logger.info("Successful authentication. Token is {}, user id is {}".format(session_token, user_id))

        # Updating user fields
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
    """ Answers whether an existing FS account binding process was completed.

    :request_field integer user_id: BotMother user platform_id.

    :response_field boolean auth_success: Whether user completed FS account binding.
    :response_field boolean success
    """

    user_id = int(request.POST['user_id'])

    if BotUser.objects.filter(bot_user_id=user_id).first() is None:
        return JsonResponse({"success": False, "error": "User with this id doesn't exist"})
    elif BotUser.objects.get(bot_user_id=user_id).fatsecret_account == "OLD":
        return JsonResponse({"success": True, "auth_success": True})
    else:
        return JsonResponse({"success": True, "auth_success": False})


@csrf_exempt
@api_safe_run(logger, token_required=True, fs_account_required=True)
def get_calories_today(request):
    """ Tells whether the specified user ate more or less calories than recommended today.

    :request_field integer user_id: BotMother user platform_id.

    :response_field string message: Tells to user about calories eaten today.
    :response_field boolean success
    """

    user_id = int(request.POST['user_id'])

    user = BotUser.objects.get(bot_user_id=user_id)
    session_token = user.fatsecret_oauth_token, user.fatsecret_oauth_token_secret
    fs = Fatsecret(settings.CONSUMER_KEY, settings.CONSUMER_SECRET, session_token=session_token)
    # Requesting datetime in my timezone
    dt = now().astimezone(pytz.timezone(settings.TIME_ZONE)).replace(tzinfo=None)

    # Reading recommended calories number
    with open("recommended.json") as f:
        calories_recommended = json.load(f)["calories"]

    # Requesting recent eaten food
    recent_eaten = fs.food_entries_get(date=dt)
    if not recent_eaten:
        return JsonResponse({"success": True, "message": "Похоже, сегодня вы ничего не добавляли в наш помощник."})

    # Calculating eaten calories
    calories_eaten = sum([int(food_item['calories']) for food_item in recent_eaten])

    # Answering
    if calories_eaten > calories_recommended:
        return JsonResponse({"success": True, "message": "Похоже, сегодня вы съели слишком много калорий."})
    else:
        return JsonResponse({"success": True, "message": "Сегодня вы съели не слишком много калорий."})


@csrf_exempt
@api_safe_run(logger, token_required=True, fs_account_required=True)
def recognise_image(request):
    """ Uses image recognition to return 4 possible food variants (food names and ids).

    :request_field integer user_id: BotMother user platform_id.
    :request_field string image_url: URL of the image that should be recognised.

    :response_field string[] food_names: Potential food names for the food in the image.
    :response_field string[] food_ids: Potential food ids for the food in the image.
    :response_field success
    """

    image_url = request.POST['image_url']
    user_id = int(request.POST['user_id'])

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

    # Requesting possible products on the image
    r = requests.post(food_recognition_url, data=json.dumps(api_request_body), headers=food_recognition_headers)
    response_body = r.json()
    possible_products = list(filter(lambda p: p["value"] > 0.8, response_body["outputs"][0]["data"]["concepts"]))[:4]
    possible_products = " ".join(map(lambda p: p["name"], possible_products))

    result = food_search(user_id, possible_products)
    if result:
        return JsonResponse(result)
    else:
        return JsonResponse({"success": False, "error": "Not found"})


@csrf_exempt
@api_safe_run(logger, token_required=True, fs_account_required=True)
def text_food_search(request):
    """ Uses FS food search to return 4 possible food variants (food names and ids).

    :request_field integer user_id: BotMother user platform_id.
    :request_field string search_query: Query for FS food search.

    :response_field string[] food_names: Potential food names for the food in the image.
    :response_field string[] food_ids: Potential food ids for the food in the image.
    :response_field success
    """

    user_id = int(request.POST['user_id'])
    search_query = request.POST['search_query']

    result = food_search(user_id, search_query)
    if result:
        return JsonResponse(result)
    else:
        return JsonResponse({"success": False, "error": "Not found"})


@csrf_exempt
@api_safe_run(logger, token_required=True)
def get_serving_for_food_id(request):
    """ Gets the serving we need for the specified food item.

    :request_field integer food_id: FS food_id.

    :response_field string measure: Metric serving unit (g, ml).
    :response_field string serving_id: Metric serving unit (g, ml).
    :response_field boolean success
    """

    food_id = str(request.POST['food_id'])

    fs = Fatsecret(settings.CONSUMER_KEY, settings.CONSUMER_SECRET)
    servings = fs.food_get(food_id)["servings"]["serving"]
    if isinstance(servings, dict):
        needed_serving = servings
    else:
        # Branded food, only one serving option, not list of servings
        needed_serving = servings[-1]

    measure = needed_serving["metric_serving_unit"]
    serving_id = needed_serving["serving_id"]
    return JsonResponse({"success": True, "measure": measure, "serving_id": serving_id})


@csrf_exempt
@api_safe_run(logger, token_required=True, fs_account_required=True)
def create_food_entry(request):
    """ Creates food entry in the specified user's food diary.

    :request_field integer user_id: BotMother user platform_id.
    :request_field string food_id: FS food_id.
    :request_field string serving_id: FS serving_id.
    :request_field float number_of_units: FS number_of_units.

    :response_field string entry_id: FS food_entry_id.
    :response_field boolean success
    """

    user_id = int(request.POST['user_id'])
    food_id = str(request.POST['food_id'])
    serving_id = str(request.POST['serving_id'])
    number_of_units = float(request.POST['number_of_units'])

    if number_of_units <= 0:
        return JsonResponse({"success": False, "error": "Number of units must be positive"})

    # Getting parameters for food entry creation
    user = BotUser.objects.get(bot_user_id=user_id)
    session_token = user.fatsecret_oauth_token, user.fatsecret_oauth_token_secret
    fs = Fatsecret(settings.CONSUMER_KEY, settings.CONSUMER_SECRET, session_token=session_token)
    # Requesting datetime in my timezone
    dt = now().astimezone(pytz.timezone(settings.TIME_ZONE)).replace(tzinfo=None)
    meal = hour_to_meal(dt.hour)
    entry_name = "{}: {}".format(dt.ctime(), fs.food_get(food_id)['food_name'])

    # Creating food entry in FS database
    entry_id_dict = fs.food_entry_create(food_id, entry_name, serving_id, number_of_units, meal)
    return JsonResponse({"success": True, "entry_id": entry_id_dict["value"]})
