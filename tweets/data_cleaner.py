import re
import spacy
from spacy.lang.en.stop_words import STOP_WORDS
STOP_WORDS |= {'s', 'etcetera'}

from tweets.functions import Functions

import time

class DataCleaner:

    col = 'tweet'
    # TODO: find a smart way
    excluded_tokens = ['#', '0', '000', '1', '2', '3', '4', '5', '22', '27', '11', '36', '60', '100', '128', '500', '830', '916', '941', 'one', 'two', '?', '??']

    def clean(self, df):
        df = self.remove_emojis(df)
        df = self.lowercase(df)
        df = self.expand_contractions(df)
        df = self.remove_emails(df)
        df = self.remove_urls(df)
        df = self.remove_rts(df)
        df = self.remove_mentions(df)
        df = self.remove_accents(df)
        # df = self.remove_special_chars(df)
        df = self.remove_stopwords(df)
        df = self.remove_punctuations(df)
        return df

    # 0
    def remove_emojis(self, df):
        df[self.col] = df[self.col].apply(lambda x: x.encode('ascii', 'ignore').decode('ascii'))
        return df

    # 1
    def lowercase(self, df):
        df[self.col] = df[self.col].apply(lambda x: x.lower())
        return df

    contractions = {"ain't": "am not / are not / is not / has not / have not",
                    "aren't": "are not / am not",
                    "can't": "cannot",
                    "can't've": "cannot have",
                    "'cause": "because",
                    "could've": "could have",
                    "couldn't": "could not",
                    "couldn't've": "could not have",
                    "didn't": "did not",
                    "doesn't": "does not",
                    "don't": "do not",
                    "hadn't": "had not",
                    "hadn't've": "had not have",
                    "hasn't": "has not",
                    "haven't": "have not",
                    "he'd": "he had / he would",
                    "he'd've": "he would have",
                    "he'll": "he shall / he will",
                    "he'll've": "he shall have / he will have",
                    "he's": "he has / he is",
                    "how'd": "how did",
                    "how'd'y": "how do you",
                    "how'll": "how will",
                    "how's": "how has / how is / how does",
                    "I'd": "I had / I would",
                    "I'd've": "I would have",
                    "I'll": "I shall / I will",
                    "I'll've": "I shall have / I will have",
                    "I'm": "I am",
                    "I've": "I have",
                    "isn't": "is not",
                    "it'd": "it had / it would",
                    "it'd've": "it would have",
                    "it'll": "it shall / it will",
                    "it'll've": "it shall have / it will have",
                    "it's": "it has / it is",
                    "let's": "let us",
                    "ma'am": "madam",
                    "mayn't": "may not",
                    "might've": "might have",
                    "mightn't": "might not",
                    "mightn't've": "might not have",
                    "must've": "must have",
                    "mustn't": "must not",
                    "mustn't've": "must not have",
                    "needn't": "need not",
                    "needn't've": "need not have",
                    "o'clock": "of the clock",
                    "oughtn't": "ought not",
                    "oughtn't've": "ought not have",
                    "shan't": "shall not",
                    "sha'n't": "shall not",
                    "shan't've": "shall not have",
                    "she'd": "she had / she would",
                    "she'd've": "she would have",
                    "she'll": "she shall / she will",
                    "she'll've": "she shall have / she will have",
                    "she's": "she has / she is",
                    "should've": "should have",
                    "shouldn't": "should not",
                    "shouldn't've": "should not have",
                    "so've": "so have",
                    "so's": "so as / so is",
                    "that'd": "that would / that had",
                    "that'd've": "that would have",
                    "that's": "that has / that is",
                    "there'd": "there had / there would",
                    "there'd've": "there would have",
                    "there's": "there has / there is",
                    "they'd": "they had / they would",
                    "they'd've": "they would have",
                    "they'll": "they shall / they will",
                    "they'll've": "they shall have / they will have",
                    "they're": "they are",
                    "they've": "they have",
                    "to've": "to have",
                    "wasn't": "was not",
                    "we'd": "we had / we would",
                    "we'd've": "we would have",
                    "we'll": "we will",
                    "we'll've": "we will have",
                    "we're": "we are",
                    "we've": "we have",
                    "weren't": "were not",
                    "what'll": "what shall / what will",
                    "what'll've": "what shall have / what will have",
                    "what're": "what are",
                    "what's": "what has / what is",
                    "what've": "what have",
                    "when's": "when has / when is",
                    "when've": "when have",
                    "where'd": "where did",
                    "where's": "where has / where is",
                    "where've": "where have",
                    "who'll": "who shall / who will",
                    "who'll've": "who shall have / who will have",
                    "who's": "who has / who is",
                    "who've": "who have",
                    "why's": "why has / why is",
                    "why've": "why have",
                    "will've": "will have",
                    "won't": "will not",
                    "won't've": "will not have",
                    "would've": "would have",
                    "wouldn't": "would not",
                    "wouldn't've": "would not have",
                    "y'all": "you all",
                    "y'all'd": "you all would",
                    "y'all'd've": "you all would have",
                    "y'all're": "you all are",
                    "y'all've": "you all have",
                    "you'd": "you had / you would",
                    "you'd've": "you would have",
                    "you'll": "you shall / you will",
                    "you'll've": "you shall have / you will have",
                    "you're": "you are",
                    "you've": "you have"
    }

    # 2
    def _expand_contractions(self, text, contraction_mapping=contractions):
        
        contractions_pattern = re.compile('({})'.format('|'.join(contraction_mapping.keys())), 
                                        flags=re.IGNORECASE|re.DOTALL)

        def expand_match(contraction):
            match = contraction.group(0)
            first_char = match[0]
            
            expanded_contraction = contraction_mapping.get(match)\
                                    if contraction_mapping.get(match)\
                                    else contraction_mapping.get(match.lower())
            
            try:
                expanded_contraction = first_char + expanded_contraction[1:]
            except TypeError:
                pass

            return expanded_contraction
            
        expanded_text = contractions_pattern.sub(expand_match, text)
        
        return expanded_text

    def expand_contractions(self, df):
        df[self.col] = df[self.col].apply(lambda x: self._expand_contractions(x))
        return df

    # 3
    def remove_emails(self, df):
        regex = '([a-zA-Z0-9+._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9_-]+)'
        df['emails'] = df[self.col].apply(lambda x: re.findall(regex, x))
        df[self.col] = df[self.col].str.replace(regex, '')
        return df

    # 4
    def remove_urls(self, df):
        regex_url = '(?:(?:https?|ftp):\/\/|\b(?:[a-z\d]+\.))(?:(?:[^\s()<>]+|\((?:[^\s()<>]+|(?:\([^\s()<>]+\)))?\))+(?:\((?:[^\s()<>]+|(?:\(?:[^\s()<>]+\)))?\)|[^\s`!()\[\]{};:\'".,<>?«»“”‘’]))?'
        df['urls'] = df[self.col].apply(lambda x: re.findall(regex_url, x))
        df[self.col] = df[self.col].apply(lambda x: re.sub(regex_url, '', x))
        return df

    # 5
    def remove_rts(self, df):
        regex_rt = 'RT'
        df[self.col] = df[self.col].apply(lambda x: re.sub(regex_rt, '', x, flags=re.IGNORECASE))
        return df

    # 6
    def remove_mentions(self, df):
        regex_mention = '\B@\w+'
        df['mentions'] = df[self.col].apply(lambda x: re.findall(regex_mention, x))
        df[self.col] = df[self.col].apply(lambda x: re.sub(regex_mention, '', x))
        return df

    # 7
    def remove_accents(self, df):
        func = Functions()

        df[self.col] = df[self.col].apply(lambda x: func.remove_accented_chars(x))
        return df

    # 8
    def remove_special_chars(self, df):
        df[self.col] = df[self.col].apply(lambda x: re.sub('[^a-zA-Z0-9. ]+', ' ', x))
        return df
    
    # 9
    def remove_stopwords(self, df):
        df[self.col] = df[self.col].apply(lambda x: (' '.join(t for t in x.split() if t not in STOP_WORDS)))
        return df

    # 10
    def remove_punctuations(self, df):
        func = Functions()
        df[self.col] = df[self.col].apply(lambda x: func.remove_puncts(x))
        return df

    def remove_non_entities(self, df):
        nlp = spacy.load('en_core_web_sm')
        ent_types = ["PERSON", "ORG", "PRODUCT", "PROPN", "GPE"]
        df['entities'] = df[self.col].apply(lambda x: (' '.join(ent.text for ent in nlp(x).ents if ent.label_ in ent_types)))
        return df

    def extract_entities(self, text):
        nlp = spacy.load('en_core_web_sm')
        ent_types = ["PERSON", "NORP", "FAC", "ORG", "GPE", "LOC", "PRODUCT", "EVENT", "WORK_OF_ART", "LAW", "LANGUAGE"]
        ents = ', '.join(ent.text for ent in nlp(text).ents if ent.label_ in ent_types and ent.text not in ['#', '1', '2', '3', '000', '??'])
        return ents