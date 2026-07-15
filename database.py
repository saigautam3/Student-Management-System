# import psycopg2

#def get_connection():
#    conn = psycopg2.connect(
#       host="localhost",
#        database="studentdb",
#        user="postgres",
#        password="root",
#        port="5432"
#    )
#    return conn

import os
import psycopg2


def get_connection():

    conn = psycopg2.connect(
        host=os.environ.get("dpg-d9bt8crbc2fs73b1dj50-a"),
        database=os.environ.get("studentdb_cle3"),
        user=os.environ.get("studentdb_cle3_user"),
        password=os.environ.get("HKC4gBpNhqpJRjPmWTPlUFIPIk4xMMZN"),
        port=os.environ.get("5432")
    )

    return conn