#!/usr/bin/python2

import tweepy
from bottle import run, route, template, view, request
from rpy2 import robjects
from datetime import datetime

### Load R Libraries
r = robjects.r

# Executes `R-setup.R' in our local R environment
with file("R-setup.R") as f:
    r(f.read())

### Twitter Interface
api = tweepy.API()
def get_tweets(search, n=1500):
    "Get up to 1500 tweets from the last week from twitter containing the search term"
    return tweepy.Cursor(api.search, q=search, rpp=100).items(n)

### R Interface
def getSentimentHist(queries):
    "Return the path to an image containing stacked histograms of the sentiment"
    path = "images/"+str(datetime.now())+".png"
    variables = [calcSentimentScores(query) for query in queries]
    print variables
    print ", ".join(v+".scores" for v in variables)
    robjects.globalenv["allscores"] = r["rbind"](*[r[v+".scores"] for v in variables])
    r("ggplot(data=allscores) + geom_bar(mapping=aes(x=score), binwidth=1)\
       + theme_bw() + scale_fill_brewer()")
    r("ggsave(file='%s')"%path)
    return path

def calcSentimentScores(search):
    "Calculate the score in R and return the R variable refering to the object"
    varName = getFreeRName()
    robjects.globalenv[varName+".text"] = [tweet.text for tweet in get_tweets(search)]
    robjects.globalenv[varName+".scores"] = score_sentiment(r[varName+".text"])
    robjects.globalenv[varName+".scores$Project"] = search
    return varName

def score_sentiment(text, pos_words=None, neg_words=None):
    "A wrapper around the R score.sentiment function"
    if not(pos_words): pos_words = r["pos.words"]
    if not(neg_words): neg_words = r["neg.words"]
    return r["score.sentiment"](text, pos_words, neg_words)

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
    graph = getSentimentHist([s.strip() for s in q.split(",")])
    return {"q": q, "graph": graph}

if __name__ == "__main__":
    run(host="localhost", port=8348)
