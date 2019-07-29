from django.conf import settings
from django.test import Client, TestCase

from generic.tests import test_hook


class BasicStatTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_bmi_calculator(self):
        hook1 = '/fatsecret/create_bot_user/'
        test_hook(self, hook1, 200, {"success": True}, user_id=1, token=settings.BOTMOTHER_TOKEN)

        hook2 = '/basicstat/bmi/'
        test_hook(self, hook2, 200, {'bmi': round(60 / 1.72**2), 'success': True}, mass=60, height=172, user_id=1,
                  token=settings.BOTMOTHER_TOKEN)
        test_hook(self, hook2, 200, {'bmi': round(60 / 1.72**2), 'success': True}, mass=60, height=1.72, user_id=1,
                  token=settings.BOTMOTHER_TOKEN)
        test_hook(self, hook2, 200, {'bmi': round(60 / 1.72**2), 'success': True}, mass=60, height=172.2, user_id=1,
                  token=settings.BOTMOTHER_TOKEN)
        test_hook(self, hook2, 400, {'error': 'ZeroDivisionError', 'success': False}, mass=60, height=0, user_id=1,
                  token=settings.BOTMOTHER_TOKEN)
