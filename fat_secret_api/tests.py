from django.test import Client, TestCase
from generic.tests import create_request, test_hook
from django.conf import settings
import json


def test_hook_url_creation(test_obj, hook, code, result, **request_kwargs):
    response = test_obj.client.post(hook, create_request(**request_kwargs),
                                    content_type="application/json")
    test_obj.assertEqual(response.status_code, code)
    response_data = json.loads(response.content)
    if response_data:
        url = response_data.pop('url', None)
        test_obj.assertEqual(response_data, result)
        test_obj.assertEqual(bool(url), True)
        print(url)


class FatSecretApiTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_user_creation_and_fs_attachment(self):
        hook1 = '/fatsecret/create_bot_user/'
        test_hook(self, hook1, 200, {"success": True}, user_id=1, token=settings.BOTMOTHER_TOKEN)
        hook2 = '/fatsecret/get_auth_url/'
        test_hook_url_creation(self, hook2, 200, {"success": True},
                               user_id=1, token=settings.BOTMOTHER_TOKEN)

    def test_user_creation_and_fs_creation(self):
        hook1 = '/fatsecret/create_bot_user/'
        test_hook(self, hook1, 200, {"success": True}, user_id=3, token=settings.BOTMOTHER_TOKEN)

        hook2 = '/fatsecret/create_fatsecret_profile/'
        test_hook(self, hook2, 200, {"success": True}, user_id=3, token=settings.BOTMOTHER_TOKEN)

        hook3 = '/fatsecret/get_calories_today/'
        test_hook(self, hook3, 200, {"success": True, "message": "Сегодня вы съели не слишком много калорий."},
                  user_id=3, token=settings.BOTMOTHER_TOKEN)

    def test_hungry_user_creation_and_fs_creation(self):
        hook1 = '/fatsecret/create_bot_user/'
        test_hook(self, hook1, 200, {"success": True}, user_id=4, token=settings.BOTMOTHER_TOKEN)

        hook2 = '/fatsecret/create_fatsecret_profile/'
        test_hook(self, hook2, 200, {"success": True}, user_id=4, token=settings.BOTMOTHER_TOKEN)

        hook3 = '/fatsecret/get_calories_today/'
        test_hook(self, hook3, 200, {"success": True,
                                     "message": "Похоже, сегодня вы ничего не добавляли в наш помощник."},
                  user_id=4, token=settings.BOTMOTHER_TOKEN)
