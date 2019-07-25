from django.conf import settings
from fatsecret import Fatsecret

from .models import BotUser


def hour_to_meal(hour):
    if 6 <= hour < 12:
        return "breakfast"
    elif 12 <= hour < 18:
        return "dinner"
    else:
        return "lunch"


def food_search(user_id, search_string):
    user = BotUser.objects.get(bot_user_id=user_id)
    session_token = user.fatsecret_oauth_token, user.fatsecret_oauth_token_secret
    fs = Fatsecret(settings.CONSUMER_KEY, settings.CONSUMER_SECRET, session_token=session_token)

    food_names = []
    food_ids = []
    try:
        results = fs.foods_search(search_string)[:4]
    except KeyError:
        return

    for food_item in results:
        food_names.append(food_item["food_name"])
        food_ids.append(food_item["food_id"])

    return {"success": True, "food_names": food_names, "food_ids": food_ids}
