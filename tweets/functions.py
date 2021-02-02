import pandas as pd
from datetime import datetime
import re
import unicodedata
import string

class Functions:

    def percentage(self, part, whole):
        return 100 * float(part) / float(whole)

    def to_df_from_json(self, tweets):
        json_data = [t._json for t in tweets]
        df = pd.json_normalize(json_data)
        return df

    def remove_url(self, text):
        url_pattern = re.compile(r'https?://\S+|www\.\S+')
        no_url = url_pattern.sub(r'', text)

        return no_url

    def remove_accented_chars(self, text):
        new_text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8', 'ignore')
        return new_text

    def remove_puncts(self, text):
        table = str.maketrans('', '', string.punctuation)
        words = str.join(' ', text.split('/')).split()        
        stripped = str.join(' ', [w.translate(table) for w in words])
        return stripped

    def convert_twitter_date(self, tw_date):
        tw_format = '%a %b %d %H:%M:%S +0000 %Y'
        std_format = '%Y-%m-%d %H:%M:%S'
        std_date = datetime.strptime(tw_date, tw_format).strftime(std_format)
        return std_date