from __future__ import absolute_import, unicode_literals

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

calory_bm_url = "https://app.botmother.com/api/bot/action/" \
                "d3-RN_UEZ/BiYClICEDgCMDoDhBZCnDkBZCBQuDoBQDglD6B3CVButDsD4DrCFD2DIDNCsDmCv"

j = {
    "platform": "any",
    "users": "everyone",
    "data": {}
}


@task()
def calories_compare():
    requests.post(calory_bm_url, json=j)
