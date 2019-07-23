from django.db import models

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
    fatsecret_oauth_token = models.CharField(max_length=100, blank=True, null=True)
    fatsecret_oauth_token_secret = models.CharField(max_length=100, blank=True, null=True)

    fs_request_token = models.CharField(max_length=100, blank=True, null=True)
    fs_request_token_secret = models.CharField(max_length=100, blank=True, null=True)
