import spacy

from tweets.twitter_api import TwitterApi
from tweets.database import Database
from tweets.functions import Functions
from tweets.analysis import Analysis

from background_task import background

@background()
def collect_data():
    db = Database()
    api = TwitterApi()
    db = Database()
    func = Functions()
    
    df_autosearch = db.get_all_autosearches()

    for i, row in df_autosearch.iterrows():
        max_id = db.get_max_tweet_id()    
        tweets = api.search(row['search_term'], since_id=max_id)        
        
        if (len(tweets) > 0):        
            df = func.to_df_from_json(tweets)

            nlp = spacy.load('en_core_web_sm')
            df['entities'] = df['text'].apply(lambda x: (', '.join(ent.text for ent in nlp(x).ents)))

            db.insert_tweets(df)

@background()
def extract_entities():
    db = Database()
    db.update_entities()

@background()
def update_dates():
    db = Database()
    db.update_dates()

@background()
def update_cooc():
    db = Database()
    analysis = Analysis()

    df_autosearch = db.get_all_autosearches()

    for i, row in df_autosearch.iterrows():
        search_term = row.search_term
        tweets = db.get_tweet_entities(search_term)

        df_cooc_matrix, df_cooc = analysis.cooccurrence(tweets, col='entities', excluded_words=[])
        db.upsert_cooc_matrix(search_term, df_cooc_matrix)
        db.upsert_cooc(search_term, df_cooc)

@background()
def update_hashtags():
    db = Database()
    db.update_hashtags()