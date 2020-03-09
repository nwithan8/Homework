#!/usr/bin/env python3

import findspark
from pyspark import *
import tweepy
from tweepy.streaming import StreamListener
from tweepy import Stream
from textblob import TextBlob
import re
import credentials

findspark.init()

conf = SparkConf().setMaster("local").setAppName("HW2")
sc = SparkContext(conf=conf)

# Twitter API Credentials
consumer_key = credentials.consumer_key
consumer_secret = credentials.consumer_secret
access_token = credentials.access_token
access_secret = credentials.access_secret

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_secret)
twitter = tweepy.API(auth)


def clean_tweet(text):
    return ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])| (\w+:\ / \ / \S+)", " ", text).split())


def get_sentiment(status):
    cleaned_tweet = clean_tweet(status.text)
    analysis = TextBlob(cleaned_tweet)
    if analysis.sentiment.polarity > 0:
        return 'positive'
    elif analysis.sentiment.polarity == 0:
        return 'neutral'
    else:
        return 'negative'


def reply_to_status(status, response, image=None):
    if image:
        twitter.update_with_media(image, '@{} {}'.format(str(status.user.screen_name), response),
                                  in_reply_to_status_id=status.id)
    else:
        twitter.update_status('@{} {}'.format(str(status.user.screen_name), response), in_reply_to_status_id=status.id)


class StdOutListener(StreamListener):

    def on_status(self, status):
        print(status.user.screen_name)
        print(get_sentiment(status))
        # do something with a new status

    def on_error(self, status_code):
        print("Error, code {}".format(status_code))


listener = StdOutListener()
stream = Stream(auth, listener)
stream.filter(track=['Trump'])
# Tweepy Documentation: http://docs.tweepy.org/en/latest/
