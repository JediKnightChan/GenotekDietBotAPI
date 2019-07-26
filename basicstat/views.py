import logging

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from generic.additional import api_safe_run

logger = logging.getLogger(__name__)


@csrf_exempt
@api_safe_run(logger)
def body_mass_index(request):
    """ Calculates body mass index.

    :request_field integer mass: One man's mass (in kg).
    :request_field integer height: One man's height (in cm).

    :response_field integer bmi: One man's calculated body mass index.
    :response_field boolean success
    """

    mass = request.POST['mass']
    height = request.POST['height']

    # If user input was in cm or it was in cm with float (like "172.2"), convert to meters
    if isinstance(height, int) or round(height) > 3:
        height /= 100
    bmi = round(mass / height**2)
    return JsonResponse({'success': True, 'bmi': bmi})
