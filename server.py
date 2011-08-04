#!/usr/bin/python2
"""\
A web interface for doing simple sentiment analysis queries of twitter.

Implements the method described at: http://jeffreybreen.wordpress.com/2011/07/04/twitter-text-mining-r-slides/ 

Usage: ./server.py
"""

__author__ = "Alex Henning"
__version__ = "0.1.dev"

import tweepy, logging
from bottle import Bottle, run, view, request, static_file
from rpy2 import robjects
from datetime import datetime

import settings as S
logging.basicConfig(filename=S.logFile, level=S.loggingLevel)


### Load R Libraries
r = robjects.r

# Executes `R-setup.R' in our local R environment
with file(S.r_setup) as r_file: r(r_file.read())

### Utils
def cacheRVariable(cacheTime):
    """A decorator for caching the results of a function for a fixed amount of time

    Specifically the function must return an R variable, that will be
    deleted from the R scope when it's time in the cache is up to
    prevent memory issues.
    """
    cache = {}
    def dec(f):
        def call(*args):
            # Clean the cache of old entries
            now = datetime.now()
            logging.info("Cleaning cache at time %s", now)
            for key, (time, val) in cache.items():
                logging.info("Checking cache of %s, the cache is %s old",
                             key, now-time)
                if (now - time) > cacheTime:
                    logging.info("Removing", key, (time, val))
                    r_query = S.r_delete_vars%{"var": val}
                    logging.info(r_query)
                    r(r_query)
                    del cache[key]

            # See if there is a cached result to return
            if args in cache.keys(): return cache[args][1]
            else:
                cache[args] = (datetime.now(), f(*args))
                return cache[args][1]
        return call
    return dec

### Twitter Interface
api = tweepy.API()
def getTweets(search, n=1500):
    "Get up to 1500 tweets from the last week from twitter containing the search term"
    return tweepy.Cursor(api.search, q=search, rpp=100).items(n)

### R Interface
def getSentimentHist(queries):
    "Return the path to an image containing stacked histograms of the sentiment"
    logging.info("Calculating histogram for: %s", (queries,))
    path = "images/"+str(datetime.now())+".png"
    variables = [calcSentimentScores(query) for query in queries]
    r_query = S.r_generate_graph%{"variables.scores": \
                                      ", ".join([i+".scores" for i in variables]),
                                  "path": path}
    logging.info(r_query)
    r(r_query)
    return path

@cacheRVariable(S.cache_time)
def calcSentimentScores(search):
    "Calculate the score in R and return the R variable refering to the object"
    varName = getFreeRName()
    tweets = [tweet.text for tweet in getTweets(search)]
    tweets = robjects.StrVector(tweets if tweets else ["Neutral"])
    r_query = S.r_calculate_sentiment%{"var": varName,
                                       "tweet_text": tweets.r_repr(),
                                       "search": search}
    logging.info(r_query)
    r(r_query)
    return varName

def getFreeRName():
    "Returns an R variable name not currently in use"
    getFreeRName.count += 1
    return "twit_sent_var_"+str(getFreeRName.count)
getFreeRName.count = 0
    
### Web Interface
app = Bottle(catchall=False)

@app.route("/")
@view(S.mainTemplate)
def twitterSentimentQuery():
    "Returns the main page and handle form dat submits"
    q = request.GET.get("q", None)
    if q:
        logging.info("Getting graph")
        graph = getSentimentHist([s.strip() for s in q.split(",")])
        logging.info("Path to graph: %s"%(graph))
    return {"q": q if q else S.defaultSearch,
            "graph": graph if q else S.defaultImage}

@app.route("/static/:path")
def serveStaticMedia(path):
    "Serves static media when requested"
    return static_file(path, root="static/")

@app.route("/images/:image")
def serveImage(image):
    "Serves images when requested"
    return static_file(image, root=S.imagePath)

if __name__ == "__main__":
    run(app, host=S.host, port=S.port)
