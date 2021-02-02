from django.db import models
from datetime import datetime

class Tweet(models.Model):
    tweet_id = models.BigIntegerField()
    tweet = models.CharField(max_length=240)
    sentiment = models.FloatField(null=True)
    unix = models.CharField(max_length=50)
    created_at = models.DateTimeField(null=True)

    def __str__(self):
        return self.tweet

class Search(models.Model):
    search_term = models.CharField(max_length=100)
    user_id = models.IntegerField()
    created_at = models.DateTimeField(default=datetime.now, blank=True)

class AutoSearch(models.Model):
    search_term = models.CharField(max_length=100)
    user_id = models.IntegerField()
    created_at = models.DateTimeField(default=datetime.now, blank=True)