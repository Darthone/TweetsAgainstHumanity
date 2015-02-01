import tweepy


def setup():
    CONSUMER_KEY = '##KEYS REMOVED##'
    CONSUMER_SECRET = '##KEYS REMOVED##'  # Make sure access level is Read And Write in the Settings tab
    ACCESS_KEY = '##KEYS REMOVED##'
    ACCESS_SECRET = '##KEYS REMOVED##'
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)
    return tweepy.API(auth)
