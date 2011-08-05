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

# The R code that adds extra words for the sentiment analysis
r_setup_sentiment = """\
    pos.words <- c(hu.liu.pos, %(pos.words)s)
    neg.words <- c(hu.liu.neg, %(neg.words)s)
"""

# The R code for creating the list of sentiment scores from the tweets
r_calculate_sentiment = """\
    %(var)s.text <- %(tweet_text)s
    %(var)s.scores <- score.sentiment(%(var)s.text, pos.words, neg.words)
"""

# The R code that set the projects label on the graph
r_set_var_project = '%(var)s.scores$Project = "%(project)s"'


# The R code for creating the histogram of the resulting scores
r_generate_graph = """\
    allscores <- rbind(%(variables.scores)s)
    png(file="%(path)s")
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
