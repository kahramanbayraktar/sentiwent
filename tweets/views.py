from django.shortcuts import render

from tweets.database import Database

def index(request):
    db = Database()
    df = db.connect()

    users = ''
    for i, row in df.iterrows():
        print(row['username'])
        users += row['username'] + ' '

    context = {
        'users': users
    }

    return render(request, 'tweets/index.html', context)