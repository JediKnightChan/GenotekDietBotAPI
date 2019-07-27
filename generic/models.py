from django.db import models
from phonenumber_field.modelfields import PhoneNumberField


FAT_SECRET_ACCOUNT = [
    ('NO', 'NO'),
    ('NEW', 'NEW'),
    ('OLD', 'OLD')
]


class BotUser(models.Model):
    bot_user_id = models.BigIntegerField(unique=True)
    fatsecret_account = models.CharField(
        max_length=3,
        choices=FAT_SECRET_ACCOUNT,
        default='NO'
    )

    phone_number = PhoneNumberField(region="RU", blank=True, null=True, unique=True)
    phone_number_verified = models.BooleanField(default=False)
    # How many times user changed unverified phone numbers at verification stage
    phones_changed_at_auth = models.IntegerField(default=0)
    phone_verification_code = models.CharField(blank=True, null=True, max_length=10)
    # How many times user changed codes at verification stage
    codes_changed_at_auth = models.IntegerField(default=0)
    # Last time when user tried to change code or unverified phone number
    last_phone_auth_try = models.DateTimeField(blank=True, null=True)

    fatsecret_oauth_token = models.CharField(max_length=100, blank=True, null=True)
    fatsecret_oauth_token_secret = models.CharField(max_length=100, blank=True, null=True)

    fs_request_token = models.CharField(max_length=100, blank=True, null=True)
    fs_request_token_secret = models.CharField(max_length=100, blank=True, null=True)
