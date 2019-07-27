import logging
import phonenumbers

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import now, pytz

from generic.models import BotUser
from generic.additional import api_safe_run

from .additional import generate_verification_code, send_verification_code


logger = logging.getLogger(__name__)


@csrf_exempt
@api_safe_run(logger, token_required=True)
def create_verification_code(request):
    """ Sends verification code to the specified user and saves all required data for its further verification.

    :request_field integer user_id: BotMother user platform_id.
    :request_field string phone_number: Phone number to be verified.

    :response_field boolean success

    :special_error string error: "Try later"
    :special_error_field integer seconds_left: How many seconds left until user can use this hook again.
    """

    user_id = int(request.POST['user_id'])
    phone_number = str(request.POST['phone_number'])

    try:
        phone_number = phonenumbers.parse(phone_number, "RU")
    except phonenumbers.phonenumberutil.NumberParseException:
        return JsonResponse({"success": False, "error": "Phone number wrong"})

    if BotUser.objects.filter(bot_user_id=user_id).first() is None:
        return JsonResponse({"success": False, "error": "User with this id doesn't exist"})

    user = BotUser.objects.get(bot_user_id=user_id)
    if user.phone_number_verified:
        # User has already verified his phone
        return JsonResponse({"success": False, "error": "User with this id has verified his phone"})
    elif BotUser.objects.filter(phone_number=phone_number).first() is not None:
        confirmed_user = BotUser.objects.get(phone_number=phone_number)
        if confirmed_user.phone_number_verified:
            # Someone already verified this phone
            return JsonResponse({"success": False, "error": "This phone is already used"})
    elif user.phones_changed_at_auth > settings.MAX_PHONE_CHANGES:
        dt_now = now().astimezone(pytz.timezone(settings.TIME_ZONE))
        time_delta = dt_now - user.last_phone_auth_try
        if time_delta < settings.MIN_TD_WHEN_MAX_PHONE_CHANGES_EXCEED:
            # Too many verification requests, user should wait
            seconds_left = (settings.MIN_TD_WHEN_MAX_PHONE_CHANGES_EXCEED - time_delta).seconds
            return JsonResponse({"success": False, "error": "Try later", "seconds_left": seconds_left})

    verification_code = generate_verification_code()
    status_code, json_data = send_verification_code(verification_code, phone_number)
    if status_code != 200 or json_data['code'] != 1:
        # Couldn't send verification code
        logger.error("Code not sent to {}{}. Request body is {}. SMS API status code {}, response {}".format(
            phone_number.country_code,
            phone_number.national_number,
            request.body,
            status_code,
            json_data
        ))
        return JsonResponse({"success": False, "error": "Couldn't send code"})
    else:
        user.phone_number = phone_number
        user.phone_verification_code = verification_code
        user.phones_changed_at_auth += 1
        user.last_phone_auth_try = now().astimezone(pytz.timezone(settings.TIME_ZONE))
        user.save()

    return JsonResponse({"success": True})


@csrf_exempt
@api_safe_run(logger, token_required=True)
def check_verification_code(request):
    """ Checks verification code of the specified user.

    :request_field integer user_id: BotMother user platform_id.
    :request_field string verification_code: Verification code.

    :response_field boolean success

    :special_error string error: "Try later"
    :special_error_field integer seconds_left: How many seconds left until user can use this hook again.
    """

    user_id = int(request.POST['user_id'])
    verification_code = str(request.POST['verification_code']).strip()

    if BotUser.objects.filter(bot_user_id=user_id).first() is None:
        return JsonResponse({"success": False, "error": "User with this id doesn't exist"})

    user = BotUser.objects.get(bot_user_id=user_id)
    if user.phone_number_verified:
        # User has already verified his phone
        return JsonResponse({"success": False, "error": "User with this id has verified his phone"})
    elif user.codes_changed_at_auth > settings.MAX_CODE_CHANGES:
        dt_now = now().astimezone(pytz.timezone(settings.TIME_ZONE))
        time_delta = dt_now - user.last_phone_auth_try
        if time_delta < settings.MIN_TD_WHEN_MAX_CODE_CHANGES_EXCEED:
            # Too many verification requests, user should wait
            seconds_left = (settings.MIN_TD_WHEN_MAX_CODE_CHANGES_EXCEED - time_delta).seconds
            return JsonResponse({"success": False, "error": "Try later", "seconds_left": seconds_left})
    elif user.phone_verification_code is None:
        # No code set
        return JsonResponse({"success": False, "error": "No code"})

    # Comparing codes
    if verification_code != user.phone_verification_code:
        user.codes_changed_at_auth += 1
        user.last_phone_auth_try = now().astimezone(pytz.timezone(settings.TIME_ZONE))
        user.save()
        return JsonResponse({"success": False, "error": "Wrong code"})
    else:
        user.phone_number_verified = True
        user.save()
        return JsonResponse({"success": True})


@csrf_exempt
@api_safe_run(logger, token_required=True)
def need_phone_verification(request):
    """ Answers whether the bot user had already verified his phone.

    :request_field integer user_id: BotMother user's platform_id.

    :response_field boolean need: Whether user needs to verify his phone.
    :response_field boolean success
    """

    user_id = int(request.POST['user_id'])

    if BotUser.objects.filter(bot_user_id=user_id).first() is None:
        return JsonResponse({"success": False, "error": "User with this id doesn't exist"})

    user = BotUser.objects.get(bot_user_id=user_id)
    if user.phone_number_verified:
        # User has already verified his phone
        return JsonResponse({"success": True, "need": False})
    else:
        return JsonResponse({"success": True, "need": True})
