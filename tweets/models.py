from django.db import models
from datetime import datetime

class AutoSearch(models.Model):
    search_term = models.CharField(max_length=100)
    user_id = models.IntegerField()
    created_at = models.DateTimeField(null=False, default=datetime.now)

class Cooc(models.Model):
    search_term = models.CharField(max_length=100, null=False)
    source = models.CharField(max_length=100, null=False)
    target = models.CharField(max_length=100, null=False)    
    weight = models.IntegerField(null=False)
    created_at = models.DateTimeField(null=False, default=datetime.now)

class CoocMatrix(models.Model):
    search_term = models.CharField(max_length=100, null=False)
    matrix = models.TextField(null=False)
    created_at = models.DateTimeField(null=False, default=datetime.now)

class Hashtag(models.Model):
    hashtag = models.CharField(max_length=100)
    count = models.IntegerField(null=False)
    created_at = models.DateTimeField(null=False, default=datetime.now)

class Search(models.Model):
    search_term = models.CharField(max_length=100)
    user_id = models.IntegerField()
    created_at = models.DateTimeField(null=False, default=datetime.now)
    
class Tweet(models.Model):
    tweet_id = models.BigIntegerField()
    tweet = models.CharField(max_length=240)
    sentiment = models.FloatField(null=True)
    unix = models.CharField(max_length=50)
    created_at = models.DateTimeField(null=True)
    entities = models.CharField(max_length=500, default='None')
    entities_extracted = models.BooleanField(default=False)

    def __str__(self):
        return self.tweet