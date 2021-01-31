from django.db import connection

import pandas as pd

class Database:

    def connect(self):
        try:
            df = pd.read_sql("SELECT * FROM auth_user", connection)
            return df
        except (Exception) as error:
            print(error)
        finally:
            if connection is not None:
                connection.close()