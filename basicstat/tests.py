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
        hook = '/basicstat/bmi/'
        test_hook(self, hook, 200, {'bmi': round(60 / 1.72**2)}, mass=60, height=172)
        test_hook(self, hook, 200, {'bmi': round(60 / 1.72**2)}, mass=60, height=1.72)
        test_hook(self, hook, 200, {'bmi': round(60 / 1.72**2)}, mass=60, height=172.2)
        test_hook(self, hook, 500, {'error': 'ZeroDivisionError: Height is 0'}, mass=60, height=0)
