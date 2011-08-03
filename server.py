#!/usr/bin/python2

from bottle import run, route, template, view, request

@route("/")
@view("twitter-sentiment-query.html")
def twitterSentimentQuery():
    q = request.GET.get("q", "@github, #gitorious, git meetup")
    queries = [s.strip() for s in q.split(",")]
    return {"q": q}

if __name__ == "__main__":
    run(host="localhost", port=8348)
