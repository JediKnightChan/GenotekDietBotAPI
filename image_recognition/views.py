import json
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

import logging

logger = logging.getLogger(__name__)
food_recognition_url = 'https://api.clarifai.com/v2/models/bd367be194cf45149e75f01d59f77ba7/outputs'
food_recognition_headers = {
    "Content-Type": "application/json",
    "Authorization": "Key {}".format(settings.FOOD_RECOGNITION_API_KEY),
}


@csrf_exempt
def recognise_image(request):
    request_body = request.body.decode("utf-8")
    request_data = json.loads(request_body)
    image_url = request_data['image_url']

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
    possible_products = filter(lambda p: p["value"] > 0.75, response_body["outputs"][0]["data"]["concepts"])
    possible_products = ", ".join(map(lambda p: p["name"], possible_products))

    return JsonResponse({"products": possible_products})

