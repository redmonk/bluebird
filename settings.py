import datetime, logging

### Server Settings  ############################################################
# The host and port to bind the server to
host = "192.168.1.3"
port = 8348

### Application Settings  #######################################################
# The path to save images in
imagePath = "images/"

# The default search to display in the textbox
defaultImage = "happy, sad"
# The default image to display when the showing the page with no query
defaultSearch = "images/example.png"

# The file containing the html template for the app
mainTemplate = "twitter-sentiment-query.html"

# Time to cache twitter results
cache_time = datetime.timedelta(days=1)

# Logging settings
logFile = "server.log"
loggingLevel = logging.DEBUG

### R Code & Settings  ###########################################################
# R file containing the setup code (load libraries and define score.sentiment)
r_setup = "R-setup.R"

# The R code for creating the list of sentiment scores from the tweets
r_calculate_sentiment = """\
    %(var)s.text <- %(tweet_text)s
    %(var)s.scores <- score.sentiment(%(var)s.text, pos.words, neg.words)
    %(var)s.scores$Project = "%(search)s"
"""

# The R code for creating the histogram of the resulting scores
r_generate_graph = """\
    allscores <- rbind(%(variables.scores)s)
    ggplot(data=allscores) + geom_bar(mapping=aes(x=score, fill=Project),\
        binwidth=1) + facet_grid(Project~.) + theme_bw()\
     + scale_fill_brewer()
    ggsave(file="%(path)s")
    dev.off()
"""

# The R code to delete variables
r_delete_vars = """\
    rm(%(var)s.text)
    rm(%(var)s.scores)
""" 
