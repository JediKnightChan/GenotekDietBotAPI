from __future__ import absolute_import, unicode_literals

from django.conf import settings

import requests
from celery import task


@task()
def task_number_one():
    print("I am task one!")


j = {
    "platform": "any",
    "users": "everyone",
    "data": {}
}


@task()
def calories_compare():
    requests.post(settings.CALORIES_HOOK, json=j)
