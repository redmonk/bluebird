import datetime, logging

### Server Settings  ############################################################
# The host and port to bind to when serving webpages.
host = "192.168.1.3"
port = 8348

### Application Settings  #######################################################
# The path to save generated images in.
imagePath = "images/"

# The default search to display in the search box.
defaultSearch = "happy, sad"
# The default image to display as an example when the showing the page
# with no query.
defaultImage = "images/example.png"

# The file containing the html template for blue bird.
mainTemplate = "bluebird.html"

# Time to cache results for.
cache_time = datetime.timedelta(days=1)

# Logging settings
logFile = "bluebird.log"
loggingLevel = logging.DEBUG

### R Code & Settings  ###########################################################
# R file containing the setup code (load libraries, define
# score.sentiment and any other helper functions)
r_setup = "R-setup.R"

# The R code that adds extra words for the sentiment analysis. Extra
# positive words can be included with %(pos.words)s and extra negative
# words can be included with %(neg.words)s.
r_setup_sentiment = """\
    pos.words <- c(hu.liu.pos, %(pos.words)s)
    neg.words <- c(hu.liu.neg, %(neg.words)s)
"""

# The R code for creating the list of sentiment scores from the
# tweets. %(var)s is the name of the variable to calculate the score
# for and %(tweet_text)s is a StrVector of the text of the tweets.
r_calculate_sentiment = """\
    %(var)s.scores <- score.sentiment(%(tweet_text)s, pos.words, neg.words)
"""

# The R code that set the projects label on the graph. %(var)s is the
# name of the variable to set the project name of and %(project)s is
# the name of the project.
r_set_var_project = '%(var)s.scores$Project = "%(project)s"'

# The R code for creating the histogram of the resulting
# scores. %(variables.scores)s is a comma seperated list of all the
# variables to graph and %(path)s is the path to save the graph to.
r_generate_graph = """\
    allscores <- rbind(%(variables.scores)s)
    png(file="%(path)s")
    ggplot(data=allscores) + geom_bar(mapping=aes(x=score, fill=Project),\
        binwidth=1) + facet_grid(Project~.) + theme_bw()\
     + scale_fill_brewer()
    ggsave(file="%(path)s")
    dev.off()
"""

# The R code to delete variables. %(var)s is the variable to delete.
r_delete_vars = """\
    rm(%(var)s.scores)
""" 
