import tweepy
from tweepy.auth import OAuthHandler

import os
import json
import time
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured
import requests
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

api_key = config('TW_API_KEY')
api_key_secret = config('TW_API_KEY_SECRET')
access_token = config('TW_ACCESS_TOKEN')
access_token_secret = config('TW_ACCESS_TOKEN_SECRET')

class TwitterApi:

    def search(self, search_term, since_id=0, max=1000):
        auth = OAuthHandler(api_key, api_key_secret)
        auth.set_access_token(access_token, access_token_secret)

        api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)

        q = search_term + ' -filter:retweets'

        tweets = [status for status in tweepy.Cursor(api.search, q=q, since_id=since_id, lang='en').items(max)]
        return tweets