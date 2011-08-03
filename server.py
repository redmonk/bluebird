#!/usr/bin/python2

import tweepy
from bottle import run, route, template, view, request, static_file
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
    print "Calculating histogram for: %s"%(queries,)
    path = "images/"+str(datetime.now())+".png"
    variables = [calcSentimentScores(query) for query in queries]
    r_query = """\
              allscores <- rbind(%(variables.scores)s)
              ggplot(data=allscores) + geom_bar(mapping=aes(x=score, fill=Project),\
              binwidth=1) + facet_grid(Project~.) + theme_bw() + scale_fill_brewer()
              ggsave(file="%(path)s")
              """%{"variables.scores": ", ".join([i+".scores" for i in variables]),
                   "path": path}
    print r_query
    r(r_query)
    return path

def calcSentimentScores(search):
    "Calculate the score in R and return the R variable refering to the object"
    varName = getFreeRName()
    tweets = [tweet.text for tweet in get_tweets(search)]
    tweets = robjects.StrVector(tweets if tweets else ["Neutral"])
    r_query = """\
              %(var)s.text <- %(tweet_text)s
              %(var)s.scores <- score.sentiment(%(var)s.text, pos.words, neg.words)
              %(var)s.scores$Project = "%(search)s"
              """%{"var": varName, "tweet_text": tweets.r_repr(), "search": search}
    print r_query
    r(r_query)
    return varName

def getFreeRName():
    "Returns an R variable name not currently in use"
    getFreeRName.count += 1
    return "twit_sent_var_"+str(getFreeRName.count)
getFreeRName.count = 0
    
### Web Interface
@route("/")
@view("twitter-sentiment-query.html")
def twitterSentimentQuery():
    "Returns the main page and handle form dat submits"
    q = request.GET.get("q", None)
    if q:
        print "Getting graph"
        graph = getSentimentHist([s.strip() for s in q.split(",")])
        print "Path to graph: %s"%(graph)
    return {"q": q if q else "happy, sad",
            "graph": graph if q else "images/example.png"}

@route("/images/:image")
def serveImage(image):
    "Serves images when requested"
    return static_file(image, root="images/")

if __name__ == "__main__":
    run(host="localhost", port=8348)
