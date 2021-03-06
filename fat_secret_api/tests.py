import json

from django.conf import settings
from django.test import Client, TestCase

from generic.tests import create_request, test_hook, test_not_constant_hook

from .additional import hour_to_meal


class FatSecretApiTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_hour_to_meal(self):
        self.assertEqual(hour_to_meal(5), "lunch")
        self.assertEqual(hour_to_meal(11), "breakfast")
        self.assertEqual(hour_to_meal(12), "dinner")
        self.assertEqual(hour_to_meal(17), "dinner")
        self.assertEqual(hour_to_meal(18), "lunch")
        self.assertEqual(hour_to_meal(0), "lunch")

    def test_user_creation_and_fs_attachment(self):
        hook1 = '/fatsecret/create_bot_user/'
        test_hook(self, hook1, 200, {"success": True}, user_id=1, token=settings.BOTMOTHER_TOKEN)

        hook2 = '/fatsecret/get_auth_url/'
        test_not_constant_hook(self, hook2, 200, {"success": True}, 'url',
                               user_id=1, token=settings.BOTMOTHER_TOKEN)

    def test_hungry_user_creation_and_fs_creation(self):
        hook1 = '/fatsecret/create_bot_user/'
        test_hook(self, hook1, 200, {"success": True}, user_id=4, token=settings.BOTMOTHER_TOKEN)

        hook2 = '/fatsecret/create_fatsecret_profile/'
        test_hook(self, hook2, 200, {"success": True}, user_id=4, token=settings.BOTMOTHER_TOKEN)

        hook3 = '/fatsecret/recognise_image/'
        test_hook(self, hook3, 200, {'food_ids': ['1884', '1892', '1894', '1882'],
                                     'food_names': ['Pork and Beef Sausage',
                                                    'Smoked Pork Sausage Link',
                                                    'Smoked Pork Sausage',
                                                    'Country Style Pork Sausage'],
                                     'success': True},
                  image_url='https://www.apkholding.ru/upload/medialibrary/5cf/5cfef1ae3d03537d1c715d37414828a9.jpg',
                  user_id=4, token=settings.BOTMOTHER_TOKEN)

        hook4 = '/fatsecret/text_food_search/'
        test_hook(self, hook4, 200, {'food_ids': ['6204', '2144599', '3782349', '5563508'],
                                     'food_names': ['Tomato and Cucumber Salad with Oil and Vinegar',
                                                    'Vine-Ripened Tomato Salad',
                                                    'Lettuce Salad with Tomato',
                                                    'Tomato Cucumber Salad'],
                                     'success': True},
                  search_query="tomato salad", user_id=4, token=settings.BOTMOTHER_TOKEN)

        hook5 = '/fatsecret/get_serving_for_food_id/'
        test_hook(self, hook5, 200, {"success": True, "measure": "g", "serving_id": "50564"}, food_id=1884,
                  token=settings.BOTMOTHER_TOKEN)

        hook6 = '/fatsecret/create_food_entry/'
        test_not_constant_hook(self, hook6, 200, {"success": True}, "entry_id", user_id=4,
                               token=settings.BOTMOTHER_TOKEN,
                               food_id=1884, serving_id=50564, number_of_units=200)

        hook7 = '/fatsecret/get_calories_today/'
        test_not_constant_hook(self, hook7, 200, {'success': True}, "message",
                               user_id=4, token=settings.BOTMOTHER_TOKEN)
