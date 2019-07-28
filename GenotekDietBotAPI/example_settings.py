import os
import datetime


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'Do you need to know me?'

CALORIES_HOOK = ''

FOOD_RECOGNITION_API_KEY = 'api key'

CONSUMER_KEY = "key"
CONSUMER_SECRET = "secret"

BOTMOTHER_TOKEN = 'token'

MAX_PHONE_CHANGES = 5
MAX_CODE_CHANGES = 7

MIN_TD_WHEN_MAX_PHONE_CHANGES_EXCEED = datetime.timedelta(hours=5)
MIN_TD_WHEN_MAX_CODE_CHANGES_EXCEED = datetime.timedelta(hours=3)

PHONE_VERIFICATION_CODE_LENGTH = 9

SMS_LOGIN = 'login'
SMS_PASSWORD = 'password'
