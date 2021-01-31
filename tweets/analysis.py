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
        # nested_word_lists = [word.strip() for word in nested_word_lists if word.strip() not in excluded_words]
        nested_word_lists = [[word.strip() for word in word_list if word.strip() != '' and word.strip() not in excluded_words] for word_list in nested_word_lists]

        # Convert to a dictionary containing all words with the number of appearances
        counter = collections.Counter(itertools.chain(*nested_word_lists))

        # Convert to a dataframe
        df_freq = pd.DataFrame(counter.most_common(count), columns=['word', 'count'])
        
        return df_freq
    
    def polarity(self, text):
        analysis = TextBlob(text)
        return analysis.sentiment.polarity

    def cooccurrence(self, df, col, exclude, ngram=(1,1), count=100):
        nested_term_lists = [[term.strip() for term in term_list.lower().split(',') if term.strip() not in exclude] for term_list in df[col]]

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

    # Keep this code for possible later uses
    # def cooccurrence2(self, df, word1, count, ent_types=["PERSON", "NORP", "FAC", "ORG", "GPE", "LOC", "EVENT"]):
    #     # Clean data
    #     cleaner = DataCleaner()
    #     df = cleaner.remove_emojis(df)
    #     df = cleaner.lowercase(df)
    #     df = cleaner.remove_emails(df)
    #     df = cleaner.remove_urls(df)
    #     df = cleaner.remove_rts(df)
    #     df = cleaner.remove_stopwords(df)
    #     df = cleaner.remove_punctuations(df)

    #     nlp = spacy.load("en_core_web_sm")

    #     # punctuation = list(string.punctuation)
    #     # stop_words = stopwords.words('english') + punctuation + ['&amp;', '&amp;amp' 'another']

    #     df_counts = pd.DataFrame(columns=['word1', 'word2', 'count'])

    #     # TODO: consider only most occurred words as word2 (pull this info from database beforehand)

    #     for i, row in df.iterrows():
    #         doc = nlp(row.tweet)

    #         for ent in doc.ents:
    #             if ent.label_ in ent_types and ent.text != word1:
    #                 df_ = df_counts.loc[(df_counts["word1"] == word1) & (df_counts["word2"] == ent.text)]

    #                 cnt = 1
                    
    #                 if not df_.empty:
    #                     cnt = int(df_counts.iloc[0]['count'])
    #                     df_counts.loc[(df_counts["word1"] == word1) & (df_counts["word2"] == ent.text), ['count']] = count + 1
    #                 else:
    #                     df_counts = df_counts.append(pd.DataFrame([[word1, ent.text, count]], columns=df_counts.columns), ignore_index=True)

    #     return df_counts.sort_values('count', ascending=False).head(count)