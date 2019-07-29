import logging

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from generic.additional import api_safe_run
from generic.models import BotUser

logger = logging.getLogger(__name__)


@csrf_exempt
@api_safe_run(logger, token_required=True)
def body_mass_index(request):
    """ Calculates body mass index.

    :request_field integer user_id: BotMother user platform_id.
    :request_field integer mass: One man's mass (in kg).
    :request_field integer height: One man's height (in cm).

    :response_field integer bmi: One man's calculated body mass index.
    :response_field boolean success
    """

    user_id = int(request.POST['user_id'])
    mass = request.POST['mass']
    height = request.POST['height']

    if BotUser.objects.filter(bot_user_id=user_id).first() is None:
        return JsonResponse({'success': False, "error": "User with this id doesn't exist"})

    # If user input was in cm or it was in cm with float (like "172.2"), convert to meters
    if isinstance(height, int) or round(height) > 3:
        height /= 100
    bmi = round(mass / height**2)

    user = BotUser.objects.get(bot_user_id=user_id)
    user.bmi = bmi
    user.save()

    return JsonResponse({'success': True, 'bmi': bmi})
