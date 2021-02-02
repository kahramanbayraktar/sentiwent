from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('tweets/', views.tweets, name='tweets'),
    path('tweets/<str:search_term>', views.tweets, name='tweets'),    
    path('sentiment/', views.sentiment, name='sentiment'),
    path('sentiment/<str:search_term>', views.sentiment, name='sentiment'),
    path('bigram/', views.bigram, name='bigram'),
    path('bigram/<str:search_term>', views.bigram, name='bigram'),
    path('cooccurrence/', views.cooccurrence, name='cooccurrence'),
    path('cooccurrence/<str:search_term>', views.cooccurrence, name='cooccurrence'),
    path('frequency/', views.frequency, name='frequency'),
    path('frequency/<str:search_term>', views.frequency, name='frequency'),
    path('hashtag/', views.hashtag, name='hashtag'),
    path('hashtag/<str:search_term>', views.hashtag, name='hashtag'),
    path('search/', views.search, name='search'),
    path('search/<str:search_term>', views.search, name='search'),
    path('settings/', views.settings, name='settings'),
]
