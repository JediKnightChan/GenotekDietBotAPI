from django.test import Client, TestCase
from generic.tests import test_hook


class BasicStatTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_bmi_calculator(self):
        hook = '/basicstat/bmi/'
        test_hook(self, hook, 200, {'bmi': round(60 / 1.72**2), 'success': True}, mass=60, height=172)
        test_hook(self, hook, 200, {'bmi': round(60 / 1.72**2), 'success': True}, mass=60, height=1.72)
        test_hook(self, hook, 200, {'bmi': round(60 / 1.72**2), 'success': True}, mass=60, height=172.2)
        test_hook(self, hook, 400, {'error': 'ZeroDivisionError', 'success': False}, mass=60, height=0)
