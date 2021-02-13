import pandas as pd
import numpy as np
from textblob import TextBlob
import itertools, collections
from sklearn.feature_extraction.text import CountVectorizer

from tweets.functions import Functions
from tweets.data_cleaner import DataCleaner
import spacy

class Analysis():
    
    def sentiment(self, tweets):
        tweets['sent_label'] = tweets['sentiment'].apply(lambda x: 'pos' if x > 0 else 'neg' if x < 0 else 'neu')        
        return tweets

    def frequency(self, df, only_entities=False, excluded_words=[], count=20):
        if only_entities:
            col = 'entities'
            sep = ','
        else:
            col = 'tweet'
            sep = ' '
            cleaner = DataCleaner()
            df = cleaner.clean(df)        

        nested_word_lists = [tweet.lower().split(sep) for tweet in df[col]]

        # Exclude unwanted words
        nested_word_lists = [[word.strip() for word in word_list if word.strip() != '' and word.strip() not in excluded_words] for word_list in nested_word_lists]

        # Convert to a dictionary containing all words with the number of appearances
        counter = collections.Counter(itertools.chain(*nested_word_lists))

        # Convert to a dataframe
        df_freq = pd.DataFrame(counter.most_common(count), columns=['word', 'count'])
        
        return df_freq
    
    def polarity(self, text):
        analysis = TextBlob(text)
        return analysis.sentiment.polarity

    def cooccurrence(self, df, col, excluded_words, ngram=(1,1), count=100):
        nested_term_lists = [[term.strip() for term in term_list.lower().split(',') if term.strip() not in excluded_words] for term_list in df[col]]

        # CountVectorizer
        vectorizer = CountVectorizer(analyzer='word', ngram_range=ngram) # ngram=(1,1) for co-occurrence, ngram=(2,2) for bigrams, etc.

        # Document-Term Matrix
        term_doc_matrix = vectorizer.fit_transform(df[col])

        # Co-occurrence Matrix
        # Set column names to terms
        u = pd.get_dummies(pd.DataFrame(nested_term_lists), prefix='', prefix_sep='').sum(level=0, axis=1)

        # Create matrix (by setting row names to terms)
        df_matrix = u.T.dot(u)

        # Remove self-matches (e.g. covid19 & covid19) by setting the upper part of the matrix to 0
        df_matrix.values[np.tril(np.ones(df_matrix.shape)).astype(np.bool)] = 0

        # Reshape and filter only count > 0
        df_stack = df_matrix.stack()
        df_stack = df_stack[df_stack >= 1].rename_axis(('source', 'target')).reset_index(name='weight')

        # Sort by weight
        df_cooc = df_stack.sort_values('weight', ascending=False).head(count)

        return df_matrix, df_cooc