from django.db import models


class BotUser(models.Model):
    bot_user_id = models.BigIntegerField()
    fatsecret_oauth_token = models.CharField(max_length=100, blank=True, null=True)
    fatsecret_oauth_token_secret = models.CharField(max_length=100, blank=True, null=True)
