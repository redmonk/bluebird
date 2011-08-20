"""
Available services for Blue Bird
"""
from utils import cache
import settings as S

### Twitter Service
# The primary service that provides access to twitter using the tweepy
# API. Please use it as an example when adding additional services.
import tweepy, traceback

api = tweepy.API()

# A helper function that fetches the tweets and their full content
@cache(S.cache_time)
def getTweets(search, n=1500):
    "Get up to 1500 tweets from the last week from twitter containing the search term"
    print "Searching: `%s`"%search
    tweets = []
    try: 
        for tweet in tweepy.Cursor(api.search, q=search, rpp=100).items(n):
            tweets.append(tweet)
    except tweepy.TweepError as e:
        traceback.print_exc()
        print "WARNING: Only %s tweets fetched from twitter."%len(tweets)
    return tuple(tweets)

# This is the primary hook which is used by Blue Bird to get the list
# of text to analyze. The function takes a search term as it's
# argument. It's body then accesses the API and it returns a tuple of
# strings to analyze the sentiment of. The return has to be some form
# of iterable for the Blue Bird API.
@cache(S.cache_time)
def getTweetsText(search):
    "Return text of up to 1500 tweets from twitter search as a list"
    return tuple(tweet.text for tweet in getTweets(search))

### Provide available services
# Services to provide as options in advanced settings. Add them in the
# form ("display name", function). The first service is the default if
# advanced option are not changed.
SERVICES = [("Tweepy", getTweetsText)]

# A dictionary for fast lookup by name.
SERVICES_DICT = dict(SERVICES)
