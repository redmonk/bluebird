#!/usr/bin/python2
"""\
A web interface for doing simple sentiment analysis queries of twitter.

Provides a web interface to the method of sentiment analysis of twitter described at: http://jeffreybreen.wordpress.com/2011/07/04/twitter-text-mining-r-slides/ 

Usage: ./bluebird.py
"""

__author__ = "Alex Henning"
__version__ = "0.2.dev"

import logging
from bottle import Bottle, run, view, request, static_file
from rpy2 import robjects
from datetime import datetime

import settings as S
logging.basicConfig(filename=S.logFile, level=S.loggingLevel)

from services import SERVICES, SERVICES_DICT
from utils import cache

### Load R Libraries
r = robjects.r
# Executes `R-setup.R' in our local R environment
with file(S.r_setup) as r_file: r(r_file.read())

### Utils
def deleteRVars(key, time, val):
    """Delete the R variable, the method for doing so is described in the settings.

    Prevents memory issues with R over long runs."""
    r(S.r_delete_vars%{"var": val})

def convertCSVToTuple(string, split=","):
    """A helper function for turning a list of comma seperated values to a tuple"""
    return tuple(s.strip() for s in string.split(split))

### R Interface
@cache(S.cache_time)
def getSentimentHist(queries, service, labels, pos_words, neg_words,
                     width=6, height=6):
    """Return the path to an image containing stacked histograms of the sentiment"""
    # logging.info("Calculating histogram for: %s", (queries,))
    path = "images/"+str(datetime.now())+".png"

    # Setup the extra words in R for all sentiment calculations
    # logging.debug("Running settings.r_setup_sentiment for pos:%s neg:%s.",
    #               pos_words, neg_words)
    print S.r_setup_sentiment%{
        "pos.words": ", ".join('"'+i+'"' for i in pos_words),
        "neg.words": ", ".join('"'+i+'"' for i in neg_words)}
    r(S.r_setup_sentiment%{
        "pos.words": ", ".join('"'+i+'"' for i in pos_words),
        "neg.words": ", ".join('"'+i+'"' for i in neg_words)})

    # Calculate the sentiment scores for each query and gather the R
    # variable names that store the resulte
    variables = [calcSentimentScores(query, service, pos_words, neg_words)
                 for query in queries]

    # Set the project name in R (Done here so it doesn't break the
    # cache of calcSentimentScore, increase speed when this is the
    # only change made)
    # logging.debug("Running settings.r_set_var_project for q:%s labels:%s.",
    #               queries, labels)
    for i in range(len(variables)):
        r(S.r_set_var_project%{
                "var": variables[i],
                "project": labels[i] if i < len(labels) else queries[i]})

    # Generate the graph in R
    # logging.debug("Running settings.r_generate_graph for %s.", queries)
    print S.r_generate_graph%{"variables.scores": \
                                  ", ".join([i+".scores" for i in variables]),
                              "path": path, "width": width, "height": height}
    r(S.r_generate_graph%{"variables.scores": \
                              ", ".join([i+".scores" for i in variables]),
                          "path": path, "width": width, "height": height})
    
    return path # Return the path to the graph

@cache(S.cache_time, deleteRVars)
def calcSentimentScores(query, service, pos_words, neg_words):
    """Calculate the score in R and return the R variable referring to the object

    query: The search to use when gathering data from the service.
    service: The service to gather information from.
    Accepts pos_words and neg_words to break the cache when they change.

    Returns: The R variable storing the sentiment score of the query.
    """
    varName = getFreeRName()
    strings = SERVICES_DICT[service](query)
    # Convert the strings to R
    rStrings = robjects.StrVector(strings if strings else ["Neutral"])

    # Calculate the sentiment in R
    # logging.debug("Running settings.r_calculate_sentiment for %s.", query)
    r(S.r_calculate_sentiment%{"var": varName,
                               "tweet_text": rStrings.r_repr(),
                               "search": query})
    return varName

def getFreeRName():
    """Returns an R variable name not currently in use"""
    getFreeRName.count += 1
    return "twit_sent_var_"+str(getFreeRName.count)
getFreeRName.count = 0
    
### Web Interface
app = Bottle(catchall=False)

@app.route("/")
@view(S.mainTemplate)
def twitterSentimentQuery():
    """Returns the main page and handle form data submits"""
    # GET all of the form data
    q = request.GET.get("q")
    labels = request.GET.get("labels")
    pos_words = request.GET.get("pos.words")
    neg_words = request.GET.get("neg.words")
    service = request.GET.get("service", SERVICES[0][0])
    if q: # If the form was submitted
        # Make the additional options are they're tuples.
        labels_tuple = convertCSVToTuple(labels) if labels else tuple()
        pos_words_tuple = convertCSVToTuple(pos_words) if pos_words else ("",)
        neg_words_tuple = convertCSVToTuple(neg_words) if neg_words else ("",)

        # Get the path to the histogram
        # logging.debug("Generating histogram...")
        graph = getSentimentHist(convertCSVToTuple(q),
                                 service=service,
                                 labels=labels_tuple,
                                 pos_words=pos_words_tuple,
                                 neg_words=neg_words_tuple,
                                 width=request.GET.get("width", "6"),
                                 height=request.GET.get("height", "6"))
        # logging.info("Path to graph: %s", graph)

    # If the request is to download the image, just download the
    # image, otherwise provide the full HTML interface.
    if request.GET.get("action") == "download":
        return static_file(graph.split("/")[-1], root=S.imagePath, download=graph)
    else:
        return {"q": q if q else S.defaultSearch,
                "labels": labels if labels else "",
                "pos_words": pos_words if pos_words else "",
                "neg_words": neg_words if neg_words else "",
                "SERVICES": SERVICES,
                "show_advanced": (labels or pos_words or neg_words or\
                                      (service != SERVICES[0][0])),
                "graph": graph if q else S.defaultImage}

# For jQuery
@app.route("/static/:path")
def serveStaticMedia(path):
    """Serves static media when requested"""
    return static_file(path, root="static/")

# Serves the generated images
@app.route("/images/:image")
def serveImage(image):
    """Serves images when requested"""
    return static_file(image, root=S.imagePath)

if __name__ == "__main__":
    # Start serving when this script is run.
    run(app, host=S.host, port=S.port)
