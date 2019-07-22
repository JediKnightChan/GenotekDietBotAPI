from django.test import Client, TestCase
import json


def create_request(**kwargs):
    return json.dumps(kwargs)


def test_hook(test_obj, hook, code, result, **request_kwargs):
    response = test_obj.client.post(hook, create_request(**request_kwargs),
                                    content_type="application/json")
    test_obj.assertEqual(response.status_code, code)
    response_data = json.loads(response.content)
    if response_data:
        test_obj.assertEqual(response_data, result)


class BasicStatTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_bmi_calculator(self):
        hook = '/food/recognise/'
        test_hook(self, hook, 200, {'products': 'sausage, meat, beef, pork, barbecue, bratwurst, vegetable'},
                  image_url='https://www.apkholding.ru/upload/medialibrary/5cf/5cfef1ae3d03537d1c715d37414828a9.jpg')
