import requests
import secrets
import string
from django.conf import settings


def generate_verification_code():
    """ Generates phone verification code.
    """

    alphabet = string.digits
    code = ''.join(secrets.choice(alphabet) for i in range(settings.PHONE_VERIFICATION_CODE_LENGTH))
    return code


def send_verification_code(code, phone):
    """ Sends phone verification code via API.

    :param code: Phone verification code.
    :type code: str
    :param phone: Phone number.
    :type phone: phonenumbers.PhoneNumber
    """

    url = "https://lcab.sms-uslugi.ru/lcabApi/sendSms.php"
    j = {
        "login": settings.SMS_LOGIN,
        "password": settings.SMS_PASSWORD,
        "txt": "Ваш код верификации в Genotek Diet Bot: {}".format(code),
        "to": "{}{}".format(phone.country_code, phone.national_number)
    }

    r = requests.post(url, data=j)
    return r.status_code, r.json()
