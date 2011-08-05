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
def cache(cacheTime, removeFunc=lambda key, time, val: None):
    """A decorator for caching the results of a function for a fixed amount of time

    All arguments and returned values of cached functions must be
    hashable, otherwise you will get errors. Written to be generic
    enough to interact with R and delete those variables if necessary
    by accepting a function that is called when an object is removed
    from the cache.

    Usage:
    @cache(datetime.timedelta(days=1))
    @cache(datetime.timedelta(days=1), f)
    """
    cache = {}
    def dec(f):
        def call(*args, **kwargs):
            # Clean the cache of old entries
            now = datetime.now()
            logging.info("%s: Cleaning cache at time %s", f.__name__, now)
            for key, (time, val) in cache.items():
                logging.info("Checking cache of %s, the cache is %s old",
                             key, now-time)
                if (now - time) > cacheTime:
                    logging.info("%s: Removing %s %s", f.__name__,key, (time, val))
                    removeFunc(key, time, val)
                    del cache[key]

            # See if there is a cached result to return
            key = (args, tuple(kwargs.items()))
            print f.__name__, key
            if key in cache.keys(): return cache[key][1]
            else:
                cache[key] = (datetime.now(), f(*args, **kwargs))
                return cache[key][1]
        return call
    return dec

def deleteRVars(key, time, val):
    "Delete var.text and var.score"
    r_query = S.r_delete_vars%{"var": val}
    logging.info(r_query)
    r(r_query)

### Twitter Interface
api = tweepy.API()
@cache(S.cache_time)
def getTweets(search, n=1500):
    "Get up to 1500 tweets from the last week from twitter containing the search term"
    return tuple(tweepy.Cursor(api.search, q=search, rpp=100).items(n))

### R Interface
@cache(S.cache_time)
def getSentimentHist(queries, labels, pos_words, neg_words):
    "Return the path to an image containing stacked histograms of the sentiment"
    logging.info("Calculating histogram for: %s", (queries,))
    path = "images/"+str(datetime.now())+".png"

    # Setup the extra words
    r_query = S.r_setup_sentiment%{
        "pos.words": ", ".join('"'+i+'"' for i in pos_words),
        "neg.words": ", ".join('"'+i+'"' for i in neg_words)}
    logging.info(r_query)
    r(r_query)
    
    variables = [calcSentimentScores(query, pos_words, neg_words)
                 for query in queries]
    for i in range(len(variables)):
        r_query = S.r_set_var_project%{
            "var": variables[i],
            "project": labels[i] if i < len(labels) else queries[i]}
        logging.info(r_query)
        r(r_query)

    
    r_query = S.r_generate_graph%{"variables.scores": \
                                      ", ".join([i+".scores" for i in variables]),
                                  "path": path}
    logging.info(r_query)
    print "Graphing..."; t = datetime.now()
    r(r_query)
    print "It took %s to graph the results."%(datetime.now()-t)
    return path

@cache(S.cache_time, deleteRVars)
def calcSentimentScores(search, pos_words, neg_words):
    """Calculate the score in R and return the R variable refering to the object

    Accepts pos_words and neg_words to break the cache.
    """
    varName = getFreeRName()
    print "Handling %s"%(search); t = datetime.now()
    tweets = [tweet.text for tweet in getTweets(search)]
    print "It took %s to fetch %s tweets"%(datetime.now()-t, len(tweets)); t = datetime.now()
    tweets = robjects.StrVector(tweets if tweets else ["Neutral"])
    r_query = S.r_calculate_sentiment%{"var": varName,
                                       "tweet_text": tweets.r_repr(),
                                       "search": search}
    logging.info(r_query)
    print "It took %s to log %s tweets"%(datetime.now()-t, len(tweets)); t = datetime.now()
    r(r_query)
    print "It took %s to to analyze %s tweets"%(datetime.now()-t, len(tweets))
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
    q = request.GET.get("q")
    labels = request.GET.get("labels")
    pos_words = request.GET.get("pos.words")
    neg_words = request.GET.get("neg.words")
    if q:
        # Make the additional options are they're lists
        labels_list = tuple(s.strip() for s in labels.split(","))\
            if labels else tuple()
        pos_words_list = tuple(s.strip() for s in pos_words.split(","))\
            if pos_words else ("",)
        neg_words_list = tuple(s.strip() for s in neg_words.split(","))\
            if neg_words else ("",)
        
        logging.info("Getting graph")
        t = datetime.now()
        graph = getSentimentHist(tuple(s.strip() for s in q.split(",")),
                                 labels=labels_list,
                                 pos_words=pos_words_list,
                                 neg_words=neg_words_list)
        print "It took %s for the whole process."%(datetime.now()-t)
        logging.info("Path to graph: %s", graph)
    return {"q": q if q else S.defaultSearch,
            "labels": labels if labels else "",
            "pos_words": pos_words if pos_words else "",
            "neg_words": neg_words if neg_words else "",
            "show_advanced": (labels or pos_words or neg_words),
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
