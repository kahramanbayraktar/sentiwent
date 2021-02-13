import pandas as pd
from datetime import datetime
import spacy
from urllib.parse import urlencode

from django.http import HttpResponse
from django.urls import reverse
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.gis import serializers
from django.core.exceptions import ValidationError

from tweets.twitter_api import TwitterApi
from tweets.database import Database
from tweets.functions import Functions
from tweets.analysis import Analysis
from tweets.visuals import Visualization
from tweets.data_cleaner import DataCleaner
from tweets.background_tasks import collect_data, update_hashtags, update_cooc

DEF_SEARCH_TERM = 'covid19'

@login_required
def index(request):
    db = Database()
    vis = Visualization()
    
    searches = db.get_searches(request.user.id)
    stats = db.get_dashboard_stats(request.user.id)
    df_hashtags = db.get_hashtags_offline()

    graphic = ''

    if len(df_hashtags.index) > 0:
        graphic = vis.word_cloud(df_hashtags)

    context = {
        'searches': searches,
        'tweet_count': stats['tweet_count'][0],
        'search_term_count': stats['search_term_count'][0],
        'min_tweet_date': stats['min_tweet_date'][0],
        'max_tweet_date': stats['max_tweet_date'][0],
        'graphic': graphic,
    }

    return render(request, 'tweets/index.html', context)

@login_required
def tweets(request, search_term=None):
    start = datetime.now()

    search_term = extract_search_term(request, search_term)
    start_date = request.POST.get('start_date', None)
    end_date = request.POST.get('end_date', None)
    tweet_count = request.POST.get('tweet_count', None)
    if tweet_count:
        tweet_count = int(tweet_count.replace(',', ''))

    db = Database()

    tweets = pd.DataFrame()
    if search_term or request.method == "POST":
        tweets = db.get_tweets(search_term, start_date, end_date, max=tweet_count)

    first_tweet_date = ''
    last_tweet_date = ''

    if not tweets.empty:
        tweets['sentiment'] = tweets['sentiment'].apply(lambda x: (round(x, 2)))
        tweets['sent'] = tweets['sentiment'].apply(lambda x: ("pos" if x > 0 else "neg" if x < 0 else "neu"))
        tweets['sent_icon_class'] = tweets['sentiment'].apply(lambda x: ("smile" if x > 0 else "frown" if x < 0 else "meh"))
        tweets['sent_color_class'] = tweets['sentiment'].apply(lambda x: ("success" if x > 0 else "danger" if x < 0 else "muted"))

        tweet_count = len(tweets.index)
        first_tweet_date = pd.to_datetime(tweets.min()['created_at'])
        last_tweet_date = pd.to_datetime(tweets.max()['created_at'])

    context = {
        'search_term': search_term if search_term else '-',
        'tweets': tweets,
        'tweet_count': tweet_count,
        'first_tweet_date': first_tweet_date if first_tweet_date else '-', 
        'last_tweet_date': last_tweet_date if last_tweet_date else '-',
        'time_elapsed': (datetime.now() - start).seconds,
    }

    return render(request, 'tweets/tweets.html', context)

@login_required
def search(request, search_term=None):
    api = TwitterApi()
    db = Database()
    func = Functions()
    analysis = Analysis()
    vis = Visualization()

    search_term = request.GET.get('search_term')
    include_synonyms = request.GET.get('include_synonyms')
    save_search = request.GET.get('save_search')
    save_tweets = request.GET.get('save_tweets')
    repeatable = request.GET.get('repeatable')

    if not search_term:
        return render(request, 'tweets/search.html')

    # TODO: Duplicate code: See background_task.py collect_data.
    max_id = db.get_max_tweet_id()

    # Step 2
    tweets = api.search(search_term, max=10, since_id=max_id)  

    # Step 3
    if (len(tweets) > 0):
        df = func.to_df_from_json(tweets)

        nlp = spacy.load('en_core_web_sm')
        df['entities'] = df['text'].apply(lambda x: (', '.join(ent.text for ent in nlp(x).ents)))

        db.insert_tweets(df)

        # Step 4
        if save_search == 'on':
            db.insert_search(search_term, request.user.id)

    context = {
        'search_term': search_term
    }

    url = reverse('index')
    return redirect(url)

@login_required
def frequency(request, search_term=None):
    start = datetime.now()
    
    search_term = extract_search_term(request, search_term)
    start_date = request.POST.get('start_date', None)
    end_date = request.POST.get('end_date', None)
    tweet_count = request.POST.get('tweet_count', None)
    if tweet_count:
        tweet_count = int(tweet_count.replace(',', ''))
    result_size = request.POST.get('result_size', None)
    if result_size:
        result_size = int(result_size.replace(',', ''))

    db = Database()
    analysis = Analysis()
    vis = Visualization()
    cleaner = DataCleaner()

    tweets = pd.DataFrame()
    if search_term or request.method == "POST":
        tweets = db.get_tweets(search_term, start_date, end_date, tweet_count)

    script = ''
    div = ''
    first_tweet_date = ''
    last_tweet_date = ''
    
    if not tweets.empty:
        excluded_words = [search_term]
        excluded_words += cleaner.excluded_tokens
        df = analysis.frequency(df=tweets, excluded_words=excluded_words, count=result_size)
        
        script, div = vis.frequency(df, search_term)

        tweet_count = len(tweets.index)
        result_size = len(df.index)
        first_tweet_date = datetime.strftime(tweets.min()['created_at'], '%m/%d/%Y %H:%M')
        last_tweet_date = datetime.strftime(tweets.max()['created_at'], '%m/%d/%Y %H:%M')

    context = {
        'search_term': search_term if search_term else '-',
        'script': script,
        'div': div,
        'tweet_count': tweet_count,
        'result_size': result_size,
        'first_tweet_date': first_tweet_date if first_tweet_date else '-', 
        'last_tweet_date': last_tweet_date if last_tweet_date else '-',
        'time_elapsed': (datetime.now() - start).seconds,
    }

    return render(request, 'tweets/frequency.html', context)

@login_required
def hashtag(request, search_term=None):
    start = datetime.now()
    
    search_term = extract_search_term(request, search_term)
    start_date = request.POST.get('start_date', None)
    end_date = request.POST.get('end_date', None)
    hashtag_count = request.POST.get('hashtag_count', None)
    if hashtag_count:
        hashtag_count = int(hashtag_count.replace(',', ''))

    db = Database()
    analysis = Analysis()
    vis = Visualization()
    cleaner = DataCleaner()

    df = pd.DataFrame()
    if search_term or request.method == "POST":
        df = db.get_hashtags(search_term, max=hashtag_count)

    script = ''
    div = ''

    if not df.empty:
        script, div = vis.frequency(df, search_term)

        hashtag_count = len(df.index)

    context = {
        'search_term': search_term if search_term else '-',
        'script': script,
        'div': div,
        'hashtag_count': hashtag_count,
        'first_tweet_date': start_date if start_date else '-', 
        'last_tweet_date': end_date if end_date else '-',
        'time_elapsed': (datetime.now() - start).seconds,
    }

    return render(request, 'tweets/hashtag.html', context)

@login_required
def hashtag_network(request, search_term=None):
    start = datetime.now()
    
    search_term = extract_search_term(request, search_term)
    start_date = request.POST.get('start_date', None)
    end_date = request.POST.get('end_date', None)
    tweet_count = request.POST.get('tweet_count', None)
    if tweet_count:
        tweet_count = int(tweet_count.replace(',', ''))
    hashtag_count = request.POST.get('hashtag_count', None)
    if hashtag_count:
        hashtag_count = int(hashtag_count.replace(',', ''))

    db = Database()
    analysis = Analysis()
    vis = Visualization()
    cleaner = DataCleaner()

    df = pd.DataFrame()
    if search_term or request.method == "POST":
        tweets = db.get_tweets(search_term, start_date, end_date, tweet_count)

    script = ''
    div = ''

    if not df.empty:
        df_coocmatrix, df_cooc = analysis.cooccurrence(tweets, 'hashtag', excluded_terms=None, count=hashtag_count)

        db.upsert_coocmatrix(search_term, df_coocmatrix)
        db.upsert_cooc(search_term, df_cooc)

        html = vis.network_pyvis(df_cooc)

    context = {
        'search_term': search_term if search_term else '-',
        'script': script,
        'div': div,
        'hashtag_count': hashtag_count,
        'first_tweet_date': start_date if start_date else '-', 
        'last_tweet_date': end_date if end_date else '-',
        'time_elapsed': (datetime.now() - start).seconds,
    }

    return render(request, 'tweets/hashtag.html', context)

@login_required
def sentiment(request, search_term=None):
    start = datetime.now()
    
    search_term = extract_search_term(request, search_term)
    start_date = request.POST.get('start_date', None)
    end_date = request.POST.get('end_date', None)
    tweet_count = request.POST.get('tweet_count', None)
    if tweet_count:
        tweet_count = int(tweet_count.replace(',', ''))
    
    db = Database()
    analysis = Analysis()
    vis = Visualization()    

    tweets = pd.DataFrame()
    if search_term or request.method == "POST":
        tweets = db.get_tweets(search_term, start_date, end_date, tweet_count)

    script = ''
    div = ''
    first_tweet_date = ''
    last_tweet_date = ''

    if not tweets.empty:
        computed_tweets = analysis.sentiment(tweets)
        script, div = vis.plot_daily_sentiment(computed_tweets)

        tweet_count = len(tweets.index)
        first_tweet_date = datetime.strftime(tweets.min()['created_at'], '%m/%d/%Y %H:%M')
        last_tweet_date = datetime.strftime(tweets.max()['created_at'], '%m/%d/%Y %H:%M')

    context = {
        'search_term': search_term if search_term else '-',
        'tweets': tweets,
        'script': script,
        'div': div,
        'tweet_count': tweet_count, 
        'first_tweet_date': first_tweet_date if first_tweet_date else '-', 
        'last_tweet_date': last_tweet_date if last_tweet_date else '-',
        'time_elapsed': (datetime.now() - start).seconds,
    }

    return render(request, 'tweets/sentiment.html', context)

@login_required
def bigram(request, search_term=None):
    start = datetime.now()

    search_term = extract_search_term(request, search_term)
    start_date = request.POST.get('start_date', None)
    end_date = request.POST.get('end_date', None)
    tweet_count = request.POST.get('tweet_count', None)
    if tweet_count:
        tweet_count = int(tweet_count.replace(',', ''))
    result_size = request.POST.get('result_size', None)
    if result_size:
        result_size = int(result_size.replace(',', ''))
    
    db = Database()
    vis = Visualization()
    cleaner = DataCleaner()
    analysis = Analysis()

    tweets = pd.DataFrame()
    if search_term or request.method == "POST":
        tweets = db.get_tweet_entities(search_term, start_date, end_date, tweet_count)

    html = ''
    first_tweet_date = ''
    last_tweet_date = ''
    
    if not tweets.empty:
        excluded_terms = [search_term]
        excluded_terms += cleaner.excluded_tokens
        df_coocmatrix, df_cooc = analysis.cooccurrence(tweets, 'entities', excluded_terms, ngram=(2,2), count=result_size)

        db.upsert_coocmatrix(search_term, df_coocmatrix)
        db.upsert_cooc(search_term, df_cooc)

        html = vis.network_pyvis(df_cooc)

        tweet_count = len(tweets.index)
        result_size = len(df_cooc.index)
        first_tweet_date = datetime.strftime(tweets.min()['created_at'], '%m/%d/%Y %H:%M')
        last_tweet_date = datetime.strftime(tweets.max()['created_at'], '%m/%d/%Y %H:%M')

    context = {
        'search_term': search_term if search_term else '-',
        'graphic': html,
        'tweet_count': tweet_count, 
        'result_size': result_size,
        'first_tweet_date': first_tweet_date, 
        'last_tweet_date': last_tweet_date,
        'time_elapsed': (datetime.now() - start).seconds,
    }

    return render(request, 'tweets/bigram.html', context)

@login_required
def cooccurrence(request, search_term=None):
    start = datetime.now()

    search_term = extract_search_term(request, search_term)
    start_date = request.POST.get('start_date', None)
    end_date = request.POST.get('end_date', None)
    tweet_count = request.POST.get('tweet_count', None)
    if tweet_count:
        tweet_count = int(tweet_count.replace(',', ''))
    result_size = request.POST.get('result_size', None)
    if result_size:
        result_size = int(result_size.replace(',', ''))
    
    db = Database()
    vis = Visualization()
    cleaner = DataCleaner()
    analysis = Analysis()

    tweets = pd.DataFrame()
    if search_term or request.method == "POST":
        tweets = db.get_tweet_entities(search_term, start_date, end_date, tweet_count)

    html = ''
    first_tweet_date = ''
    last_tweet_date = ''
    
    if not tweets.empty:
        # df_coocmatrix = db.get_coocmatrix(search_term)
        # df_cooc = db.get_cooc(search_term)

        # TODO: Use this approach once it runs stable
        # if df_coocmatrix.empty or df_cooc.empty:
        excluded_terms = [search_term] # TODO: more words to exclude? similar words? synonyms?
        excluded_terms += cleaner.excluded_tokens
        df_coocmatrix, df_cooc = analysis.cooccurrence(tweets, 'entities', excluded_terms, count=result_size)

        db.upsert_coocmatrix(search_term, df_coocmatrix)
        db.upsert_cooc(search_term, df_cooc)

        html = vis.network_pyvis(df_cooc)

        tweet_count = len(tweets.index)
        result_size = len(df_cooc.index)
        first_tweet_date = datetime.strftime(tweets.min()['created_at'], '%m/%d/%Y %H:%M')
        last_tweet_date = datetime.strftime(tweets.max()['created_at'], '%m/%d/%Y %H:%M')

    context = {
        'search_term': search_term if search_term else '-',
        'graphic': html,
        'tweet_count': tweet_count, 
        'result_size': result_size,
        'first_tweet_date': first_tweet_date, 
        'last_tweet_date': last_tweet_date,
        'time_elapsed': (datetime.now() - start).seconds,
    }

    return render(request, 'tweets/cooccurrence.html', context)

@login_required
def settings(request):
    db = Database()
    
    autosearch_terms = db.get_autosearches(request.user.id)

    context = {
        'autosearch_terms': autosearch_terms
    }

    if request.method == "GET" and not request.GET.get('search_term'):
        return render(request, 'tweets/settings.html', context)

    search_term = request.POST['search_term']
    if not search_term:
        search_term = DEF_SEARCH_TERM

    db.insert_autosearch(search_term, request.user.id)

    return redirect(reverse('settings'))

@login_required
def delete_auto_search(request):
    db = Database()
    
    autosearch_term = db.get_autosearch(request.id)

    if (autosearch_term):
        if(autosearch_term.user_id == request.user_id or request.user):
            db.delete_autosearch(request.id)

    return redirect(reverse('settings'))

@staff_member_required
def bgtask(request):
    # update_dates(repeat=150)
    collect_data(repeat=900)
    # extract_entities(repeat=150)
    update_hashtags(repeat=3600)
    update_cooc(repeat=7200)

    return HttpResponse("Background tasks have started.")

def extract_search_term(request, search_term, use_default=False):
    if request.method == "GET":
        if not search_term:
            search_term = request.GET.get('search_term')
            if not search_term and use_default:
                search_term = DEF_SEARCH_TERM
    else:
        search_term = request.POST['search_term']

    return search_term