#!/usr/bin/python

from bottle import run, route, template, view, request

#template("twitter-sentiment-query.html", name="twitter-sentiment-query")

@route("/")
@view("twitter-sentiment-query.html")
def twitterSentimentQuery():
    q = request.GET.get("q", "@github, #gitorious, git meetup")
    return {"q": q}

if __name__ == "__main__":
    run(host="localhost", port=8348)
