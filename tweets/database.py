from django.db import connection
import pyodbc
import traceback
import sys
import pandas as pd
import logging
from datetime import datetime as dt

from tweets.data_cleaner import DataCleaner
from tweets.analysis import Analysis
from tweets.functions import Functions

class Database:

    def insert_tweets(self, df):
        logger = logging.getLogger(__name__)

        analysis = Analysis()
        func = Functions()

        sql = "INSERT INTO tweets_tweet (tweet_id, unix, created_at, tweet, sentiment, entities, entities_extracted) VALUES(%s, %s, %s, %s, %s, %s, %s);"

        try:
            with connection.cursor() as cursor:
                for i, row in df.iterrows():                    
                    sentiment = analysis.polarity(row.text)

                    created_at = func.convert_twitter_date(row.created_at)
                    
                    cursor.execute(sql, (row.id, row.created_at, created_at, row.text, sentiment, row.entities, 1))
                connection.commit()
        except (Exception) as error:
            print(error)
            logger.error(error)
        finally:
            if connection is not None:
                connection.close()

    def get_tweets(self, search_term, start_date=None, end_date=None, max=100):
        logger = logging.getLogger(__name__)

        try:
            sql = "SELECT TOP " + str(max) + " tweet, sentiment, created_at FROM tweets_tweet WHERE tweet LIKE '%" + search_term + "%'"
            if start_date:
                sql += " AND created_at >= '{}'".format(start_date)
            if end_date:
                sql += " AND created_at <= '{}'".format(end_date)
            sql += " ORDER BY created_at DESC;"

            df = pd.read_sql(sql, connection)
            return df
        except (Exception) as error:
            print(error)
            logger.error(error)
        finally:
            if connection is not None:
                connection.close()

    def get_tweet_entities(self, search_term, start_date=None, end_date=None, max=10000, include_sentiment=False):
        logger = logging.getLogger(__name__)

        try:
            fields = " entities, created_at"
            if include_sentiment:
                fields += ", sentiment"

            sql = "SELECT TOP {}".format(max)
            sql += fields
            sql += " FROM tweets_tweet WHERE entities IS NOT NULL AND entities != ''"

            if search_term:                
                sql += " AND (entities LIKE '{}, %' OR entities LIKE '% {},%' OR entities LIKE '% {}' OR entities = '{}')"
                sql = sql.format(search_term, search_term, search_term, search_term)

            if start_date:
                sql += " AND created_at >= '" + start_date + "'"
            if end_date:
                sql += " AND created_at <= DATEADD(DAY, 1, '" + end_date + "')"

            sql += " ORDER BY created_at DESC;"

            df = pd.read_sql(sql, connection)
            return df
        except (Exception) as error:
            print(error)
            logger.error(error)
        finally:
            if connection is not None:
                connection.close()

    def get_hashtags(self, search_term, start_date=None, end_date=None, max=100):
        logger = logging.getLogger(__name__)

        try:
            sql =   "SELECT TOP {} w.VALUE word, COUNT(*) [count]" \
                    " FROM tweets_tweet AS t"\
                        " CROSS APPLY ("\
                            " SELECT DISTINCT TRIM(VALUE) [value]" \
                            " FROM STRING_SPLIT(REPLACE(REPLACE(t.tweet, CHAR(13), ' '), CHAR(10), ' '), N' ')" \
                        " ) AS w" \
                    " WHERE tweet LIKE '%{}%' AND value != '' AND VALUE LIKE '#%' AND VALUE NOT LIKE '%{}%' AND VALUE != '#'".format(max, search_term, search_term)
            if start_date:
                sql += " AND created_at >= '{}'".format(start_date)
            if end_date:
                sql += " AND created_at <= '{}'".format(end_date)
            sql +=  " GROUP BY w.VALUE" \
                    " ORDER BY COUNT(*) DESC;"

            df = pd.read_sql(sql, connection)
            return df
        except (Exception) as error:
            print(error)
            logger.error(error)
        finally:
            if connection is not None:
                connection.close()

    def get_hashtags_offline(self, max=100):
        logger = logging.getLogger(__name__)

        try:
            sql = "SELECT TOP {} hashtag, [count] FROM tweets_hashtag ORDER BY [count] DESC".format(max)
            df = pd.read_sql(sql, connection)
            return df
        except (Exception) as error:
            print(error)
            logger.error(error)
        finally:
            if connection is not None:
                connection.close()

    def insert_search(self, search_term, user_id):
        logger = logging.getLogger(__name__)

        sql = "INSERT INTO tweets_search (user_id, search_term, created_at) VALUES (%s, %s, %s);"
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql, (user_id, search_term, dt.now()))
                connection.commit()
        except (Exception) as error:
            print(error)
            logger.error(error)
        finally:
            if connection is not None:
                connection.close()

    def get_searches(self, user_id, max=5):
        logger = logging.getLogger(__name__)

        try:
            df = pd.read_sql("SELECT TOP " + str(max) +  " * FROM tweets_search WHERE user_id=" + str(user_id) + " ORDER BY created_at DESC;", connection)
            return df
        except (Exception) as error:
            print(error)
            logger.error(error)
        finally:
            if connection is not None:
                connection.close()

    def insert_autosearch(self, search_term, user_id):
        logger = logging.getLogger(__name__)

        sql = "IF NOT EXISTS(SELECT * FROM tweets_autosearch WHERE user_id = %s AND search_term = %s) "
        sql += "INSERT INTO tweets_autosearch (user_id, search_term, created_at) VALUES (%s, %s, %s)"

        try:
            with connection.cursor() as cursor:
                cursor.execute(sql, (user_id, search_term, user_id, search_term, dt.now()))
                connection.commit()
        except (Exception) as error:
            print(error)
            logger.error(error)
        finally:
            if connection is not None:
                connection.close()

    def get_all_autosearches(self):
        logger = logging.getLogger(__name__)

        try:
            df = pd.read_sql("SELECT * FROM tweets_autosearch ORDER BY search_term;", connection)
            return df
        except (Exception) as error:
            print(error)
            logger.error(error)
        finally:
            if connection is not None:
                connection.close()

    def get_autosearches(self, user_id):
        logger = logging.getLogger(__name__)

        try:
            df = pd.read_sql("SELECT * FROM tweets_autosearch WHERE user_id=" + str(user_id) + " ORDER BY search_term;", connection)
            return df
        except (Exception) as error:
            print(error)
            logger.error(error)
        finally:
            if connection is not None:
                connection.close()

    def get_autosearch(self, id):
        logger = logging.getLogger(__name__)

        try:
            df = pd.read_sql("SELECT * FROM tweets_autosearch WHERE id=" + str(id) + ";", connection)
            return df
        except (Exception) as error:
            print(error)
            logger.error(error)
        finally:
            if connection is not None:
                connection.close()

    def delete_autosearch(self, id):
        logger = logging.getLogger(__name__)

        sql = "DELETE FROM tweets_autosearch WHERE id=" + str(id) + ";"

        try:
            df = pd.read_sql(sql, connection)
            with connection.cursor() as cursor:
                cursor.execute(sql)
                connection.commit()
        except (Exception) as error:
            print(error)
            logger.error(error)
        finally:
            if connection is not None:
                connection.close()

    def get_max_tweet_id(self):
        logger = logging.getLogger(__name__)

        sql = "SELECT MAX(tweet_id) FROM tweets_tweet;"

        try:
            with connection.cursor() as cursor:
                max = cursor.execute(sql).fetchval()
                return max                
        except (Exception) as error:
            print(error)
            logger.error(error)
        finally:
            if connection is not None:
                connection.close()
        logger = logging.getLogger(__name__)

    def get_dashboard_stats(self, user_id):
        logger = logging.getLogger(__name__)

        try:
            sql = "SELECT q1.tweet_count, q2.search_term_count, q3.min_tweet_date, q4.max_tweet_date "\
                  "FROM "\
	              "(SELECT COUNT(*) tweet_count FROM tweets_tweet) q1, "\
	              "(SELECT COUNT(*) search_term_count FROM tweets_autosearch WHERE user_id = {}) q2, "\
	              "(SELECT MIN(created_at) min_tweet_date FROM tweets_tweet) q3, "\
	              "(SELECT MAX(created_at) max_tweet_date FROM tweets_tweet) q4;"
            df = pd.read_sql(sql.format(user_id), connection)
            return df
        except (Exception) as error:
            print(error)
            logger.error(error)
        finally:
            if connection is not None:
                connection.close()

    def update_entities(self):
        logger = logging.getLogger(__name__)
        cleaner = DataCleaner()

        # Get tweets with no entities extracted yet (or including no entities indeed)
        sql_list = "SELECT TOP 1000 id FROM tweets_tweet WHERE entities_extracted = 0;"
        df_tweets = pd.read_sql(sql_list, connection)
        
        try:
            with connection.cursor() as cursor:
                for i, row in df_tweets.iterrows():
                    id = row["id"]

                    # Get tweet
                    sql_get = "SELECT tweet FROM tweets_tweet WHERE id = " + str(id) + ";"
                    df_tweet = pd.read_sql(sql_get, connection)
                    
                    # Extract entities for the tweet
                    ents = cleaner.extract_entities(df_tweet['tweet'][0])
                    ents = ents.replace("'", "''")

                    # Update tweet's entities field
                    sql_upd = "UPDATE tweets_tweet SET entities = '" + ents + "', entities_extracted = 1 WHERE id = " + str(id) + ";"
                    cursor.execute(sql_upd)
                connection.commit()
        except (Exception) as error:
            print(error)
            logger.error(error)
        finally:
            if connection is not None:
                connection.close()

    def update_tweet_hashtags(self):
        logger = logging.getLogger(__name__)
        cleaner = DataCleaner()

        # Get tweets with no entities extracted yet (or including no entities indeed)
        sql_list = "SELECT TOP 1000 id FROM tweets_tweet WHERE entities_extracted = 0;"
        df_tweets = pd.read_sql(sql_list, connection)
        
        try:
            with connection.cursor() as cursor:
                for i, row in df_tweets.iterrows():
                    id = row["id"]

                    # Get tweet
                    sql_get = "SELECT tweet FROM tweets_tweet WHERE id = " + str(id) + ";"
                    df_tweet = pd.read_sql(sql_get, connection)
                    
                    # Extract entities for the tweet
                    ents = cleaner.extract_entities(df_tweet['tweet'][0])
                    ents = ents.replace("'", "''")

                    # Update tweet's entities field
                    sql_upd = "UPDATE tweets_tweet SET entities = '" + ents + "', entities_extracted = 1 WHERE id = " + str(id) + ";"
                    cursor.execute(sql_upd)
                connection.commit()
        except (Exception) as error:
            print(error)
            logger.error(error)
        finally:
            if connection is not None:
                connection.close()


    def update_dates(self):
        logger = logging.getLogger(__name__)

        func = Functions()

        sql_list = "SELECT TOP 1000 id FROM tweets_tweet WHERE created_at IS NULL;"
        df_tweets = pd.read_sql(sql_list, connection)
        
        try:
            with connection.cursor() as cursor:
                for i, row in df_tweets.iterrows():
                    id = row.id

                    # Get tweet
                    sql_get = "SELECT unix FROM tweets_tweet WHERE id = " + str(id) + ";"
                    df_tweet = pd.read_sql(sql_get, connection)
                    
                    created_at = func.convert_twitter_date(df_tweet.unix[0])

                    # Update tweet's entities field
                    sql_upd = "UPDATE tweets_tweet SET created_at = '" + created_at + "' WHERE id = " + str(id) + ";"
                    cursor.execute(sql_upd)
                connection.commit()
        except (Exception) as error:
            print(error)
            logger.error(error)
        finally:
            if connection is not None:
                connection.close()

    def upsert_cooc(self, search_term, df):
        logger = logging.getLogger(__name__)        
        try:
            with connection.cursor() as cursor:
                # Get existing cooc
                sql_get = "SELECT * FROM tweets_cooc WHERE search_term = '" + search_term + "';"
                df_cooc = pd.read_sql(sql_get, connection)

                # Delete existing cooc
                if not df_cooc.empty:
                    sql_del = "DELETE FROM tweets_cooc WHERE search_term = '" + search_term + "';"
                    cursor.execute(sql_del)

                # Insert cooc
                for i, row in df.iterrows():
                    source = row['source']
                    target = row['target']
                    weight = row['weight']
                    sql_ins = "INSERT INTO tweets_cooc (search_term, source, target, weight, created_at) VALUES (%s, %s, %s, %s, %s);"
                    cursor.execute(sql_ins, (search_term, source, target, weight, dt.now()))
                connection.commit()
        except (Exception) as error:
            print(error)
            logger.error(error)
        finally:
            if connection is not None:
                connection.close()

    def get_cooc(self, search_term):
        logger = logging.getLogger(__name__)

        try:
            sql = "SELECT * FROM tweets_cooc WHERE search_term = '" + search_term + "';"
            df = pd.read_sql(sql, connection)
            return df
        except (Exception) as error:
            print(error)
            logger.error(error)
        finally:
            if connection is not None:
                connection.close()

    def upsert_coocmatrix(self, search_term, df):
        logger = logging.getLogger(__name__)
        cleaner = DataCleaner()
        
        try:
            with connection.cursor() as cursor:
                # Get existing coocmatrix
                sql_get = "SELECT * FROM tweets_coocmatrix WHERE search_term = '" + search_term + "';"
                df_coocmatrix = pd.read_sql(sql_get, connection)

                matrix = df.to_json()

                # Update or insert coocmatrix
                if not df_coocmatrix.empty:
                    sql = "UPDATE tweets_coocmatrix SET matrix = %s WHERE search_term = %s;"
                    cursor.execute(sql, (matrix, search_term))
                else:
                    sql = "INSERT INTO tweets_coocmatrix (search_term, matrix, created_at) VALUES (%s, %s, %s);"
                    cursor.execute(sql, (search_term, matrix, dt.now()))
                connection.commit()
        except (Exception) as error:
            print(error)
            logger.error(error)
        finally:
            if connection is not None:
                connection.close()

    def get_coocmatrix(self, search_term):
        logger = logging.getLogger(__name__)

        try:
            sql = "SELECT matrix FROM tweets_coocmatrix WHERE search_term = '" + search_term + "';"
            df = pd.read_sql(sql, connection)
            matrix = df['matrix'][0]
            df = pd.read_json(matrix)
            return df
        except (Exception) as error:
            print(error)
            logger.error(error)
        finally:
            if connection is not None:
                connection.close()
    
    def update_hashtags(self):
        logger = logging.getLogger(__name__)

        try:
            sql =   "DECLARE @max_id INT;" \
                    " SELECT @max_id = MAX(id) FROM tweets_hashtag;" \
                    " SELECT w.VALUE hashtag, COUNT(*) [count], GETDATE()" \
                    " FROM tweets_tweet AS t" \
                    "    CROSS APPLY (" \
                    "        SELECT DISTINCT TRIM('…' FROM TRIM('?' FROM TRIM(',' FROM TRIM(':' FROM TRIM('.' FROM VALUE))))) [value]" \
                    "        FROM STRING_SPLIT(REPLACE(REPLACE(t.tweet, CHAR(13), ' '), CHAR(10), ' '), N' ')" \
                    "    ) AS w" \
                    " WHERE VALUE LIKE '#%' AND VALUE NOT IN ('#', '#1', '#2')" \
                    " GROUP BY w.VALUE" \
                    " ORDER BY COUNT(*) DESC;" \
                    " DELETE FROM tweets_hashtag WHERE id < @max_id;"
            with connection.cursor() as cursor:
                cursor.execute(sql)
                connection.commit()
        except (Exception) as error:
            print(error)
            logger.error(error)
        finally:
            if connection is not None:
                connection.close()