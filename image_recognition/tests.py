from django.test import Client, TestCase
from generic.tests import test_hook


class BasicStatTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_food_recognition(self):
        hook = '/food/recognise/'
        test_hook(self, hook, 200, {'products': 'sausage, meat, beef, pork, barbecue, bratwurst, vegetable'},
                  image_url='https://www.apkholding.ru/upload/medialibrary/5cf/5cfef1ae3d03537d1c715d37414828a9.jpg')
