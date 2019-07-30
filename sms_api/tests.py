import json

from django.conf import settings
from django.test import Client, TestCase

from generic.tests import test_hook, test_not_constant_hook
from generic.models import BotUser


class SmsApiTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.test_phone_number = input("Enter test phone number: ").strip()

    def test_verification_code_sending(self):
        bot_user_id = 1
        hook1 = "/fatsecret/create_bot_user/"
        test_hook(self, hook1, 200, {"success": True}, user_id=bot_user_id, token=settings.BOTMOTHER_TOKEN)

        hook2 = "/smsapi/need_phone_verification/"
        test_hook(self, hook2, 200, {"success": True, "need": True}, user_id=bot_user_id,
                  token=settings.BOTMOTHER_TOKEN)

        hook3 = "/smsapi/create_verification_code/"
        test_hook(self, hook3, 200, {"success": True}, user_id=bot_user_id, phone_number=self.test_phone_number,
                  token=settings.BOTMOTHER_TOKEN)

        verification_code = BotUser.objects.get(bot_user_id=bot_user_id).phone_verification_code
        print(verification_code)

        hook4 = "/smsapi/check_verification_code/"
        test_hook(self, hook4, 200, {"success": True}, user_id=bot_user_id,
                  verification_code="  {} ".format(verification_code), token=settings.BOTMOTHER_TOKEN)

        hook5 = "/smsapi/need_phone_verification/"
        test_hook(self, hook5, 200, {"success": True, "need": False}, user_id=bot_user_id,
                  token=settings.BOTMOTHER_TOKEN)

    def test_messing_code_check(self):
        bot_user_id = 2
        hook1 = "/fatsecret/create_bot_user/"
        test_hook(self, hook1, 200, {"success": True}, user_id=bot_user_id, token=settings.BOTMOTHER_TOKEN)

        hook2 = "/smsapi/create_verification_code/"
        test_hook(self, hook2, 200, {"success": True}, user_id=bot_user_id, phone_number=self.test_phone_number,
                  token=settings.BOTMOTHER_TOKEN)

        hook3 = "/smsapi/check_verification_code/"
        wrong_code = "1" * settings.PHONE_VERIFICATION_CODE_LENGTH
        for i in range(settings.MAX_CODE_CHANGES + 1):
            test_hook(self, hook3, 200, {"success": False, "error": "Wrong code"}, user_id=bot_user_id,
                      verification_code=wrong_code, token=settings.BOTMOTHER_TOKEN)

        test_not_constant_hook(self, hook3, 200, {"success": False, "error": "Try later"}, "seconds_left",
                               user_id=bot_user_id, verification_code=wrong_code, token=settings.BOTMOTHER_TOKEN)

    def test_zero_and_big_phone_numbers(self):
        bot_user_id = 2
        phone_zero = "000078998887777"
        phone_big = "9 906 123 45 65"

        hook1 = "/fatsecret/create_bot_user/"
        test_hook(self, hook1, 200, {"success": True}, user_id=bot_user_id, token=settings.BOTMOTHER_TOKEN)

        hook2 = "/smsapi/create_verification_code/"
        test_hook(self, hook2, 200, {'error': 'Phone number wrong', 'success': False}, user_id=bot_user_id,
                  phone_number=phone_zero, token=settings.BOTMOTHER_TOKEN)

        hook3 = "/smsapi/create_verification_code/"
        test_hook(self, hook3, 200, {'error': 'Phone number wrong', 'success': False}, user_id=bot_user_id,
                  phone_number=phone_big, token=settings.BOTMOTHER_TOKEN)


