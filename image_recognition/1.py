from fatsecret import Fatsecret
from django.conf import settings

fs = Fatsecret(settings.CONSUMER_KEY, settings.CONSUMER_SECRET)

auth_url = fs.get_authorize_url()

print("Browse to the following URL in your browser to authorize access:\n{}".format(auth_url))

pin = input("Enter the PIN provided by FatSecret: ")
session_token = fs.authenticate(int(pin))

foods = fs.foods_get_most_eaten()
print("Most Eaten Food Results: {}".format(len(foods)))