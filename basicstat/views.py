import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import logging


logger = logging.getLogger(__name__)


@csrf_exempt
def body_mass_index(request):
    try:
        request_body = request.body.decode("utf-8")
        request_data = json.loads(request_body)
        mass = request_data['mass']
        height = request_data['height']
        # If user input was in cm or it was in cm with float (like "172.2"), convert to meters
        if isinstance(height, int) or round(height) > 3:
            height /= 100
        bmi = round(mass / height**2)
        return JsonResponse({'bmi': bmi})
    except json.decoder.JSONDecodeError:
        logger.error("JSONDecodeError. Body request is {}".format(request.body))
        return JsonResponse({'error': 'JSONDecodeError: couldn\'t decode JSON'}, status=500)
    except KeyError:
        logger.error("KeyError. Body request is {}".format(request_body))
        return JsonResponse({'error': 'KeyError: mass or height parameters not found'}, status=500)
    except ZeroDivisionError:
        logger.error("ZeroDivisionError. Body request is {}".format(request_body))
        return JsonResponse({'error': 'ZeroDivisionError: Height is 0'}, status=500)
    except Exception as e:
        logger.error("Error: {}. Body request is {}".format(e, request_body))
        return JsonResponse({'error': 'Unknown error occured'}, status=500)
