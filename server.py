#!/usr/bin/python2

import tweepy
from bottle import run, route, template, view, request
    
### Twitter Interface
api = tweepy.API()
def get_tweets(search, n=1500):
    "Get up to 1500 tweets from the last week from twitter containing the search term"
    return tweepy.Cursor(api.search, q=search, rpp=100).items(n)

def getFreeRName():
    "Returns an R variable name not currently in use"
    getFreeRName.count += 1
    return "twit_sent_var_"+str(getFreeRName.count)
getFreeRName.count = 0
    
### Web Interface
@route("/")
@view("twitter-sentiment-query.html")
def twitterSentimentQuery():
    q = request.GET.get("q", "@github, #gitorious, git meetup")
    queries = [s.strip() for s in q.split(",")]
    results = [calcScores(query) for query in queries]
    return {"q": q}

if __name__ == "__main__":
    run(host="localhost", port=8348)
