# -*- coding: utf-8 -*-
__name__ = '__main__'

import time
import random
import re
import textwrap
import datetime
import os
import auth
import tweepy
import string

api = auth.setup()

rulesString = 'Tweet "cards" at me for white cards. Reply to my Black Card Tweet with a response. The Tweet with the most faves + rts wins!'
twitterHandle = "@TweetsVH"
blackCardsFile = 'blackcards.txt'
whiteCardsFile = 'whitecards.txt'

waitTime = 240  # cycles
sleepTime = 30  # seconds
tryTime = 120   # seconds


def load_cards(filename):
    ret = []
    with open(filename, 'r') as f:
        for line in f.readlines():
            ret.append(line)
    print "Loaded %s" % (filename)
    return ret


def pick_white_cards(whiteCards):
    return random.sample(whiteCards, 7)


def generate_char():
    return random.choice(string.letters)


def try_api(function):
    def wrapper(*args, **kwargs):
        tries = 5
        while tries:
            try:
                return function(*args, **kwargs)
                break
            except tweepy.TweepError as e:
                try:
                    if "Rate limit exceeded" in e[0][0]['message']:
                        print "Caught Rate Limit, while waiting for the following args: %s %s" % (str(*args), str(**kwargs))
                        time.sleep(tryTime)
                except TypeError:
                    print "Caught: %s. Done Trying" % (str(e))
                    break
            except Exception as e:
                print "Unexpected error. Exiting: " + str(e)
                exit()
            tries -= 1
    return wrapper


@try_api
def update_status(status):
    l = textwrap.wrap(status, 140)
    for e in l:
        print "Posting Status: %s" %(e)
        api.update_status(e)


@try_api
def get_status_id(num_back):
    return (api.home_timeline())[num_back].id


@try_api
def get_mentions(num):
    return api.mentions_timeline(count=num)


@try_api
def send_direct_message(user, msg):
    l = textwrap.wrap(msg, 140)
    for e in l:
        api.send_direct_message(user=user, text=e)


def main():
    i = 0
    ruleTweet = 5
    ruleCount = 0
    sentCards = []
    waiting = False
    blackCards = load_cards(blackCardsFile)
    whiteCards = load_cards(whiteCardsFile)

    while True:
        if not waiting:
            i = 0
            if not blackCards:
                blackCards = load_cards(blackCardsFile)

            print "Picking Black Card"
            currentBlackCard = random.choice(blackCards).replace("Draw 2, ", "")
            update_status(currentBlackCard)
            blackCardID = get_status_id(0)

            neededAnswers = 1
            if re.search("pick", currentBlackCard, flags=re.IGNORECASE):
                update_status('Remember to separate your responses with a semicolon(;) %s' % (generate_char()))
                neededAnswers = int(currentBlackCard[6:7])

            print "Answers Needed: %s for %s" % (neededAnswers, currentBlackCard)
            blackCards.remove(currentBlackCard)  # so that it can't be call again

            if ruleCount == 0:
                update_status(rulesString + generate_char())
                ruleCount = ruleTweet
                print "Tweeted Rules"
            ruleCount -= 1

            lastBlackTweetTime = datetime.datetime.now()
            sentCards = []
            waiting = True
            #winnerFound = False

        if waiting:
            print "Checking for card requests in all mentions"
            #check for card requests
            mentions = get_mentions(200)
            for mention in mentions:
                print "%s: %s %s" % (mention.user.screen_name, mention.text, mention.created_at)
                #send out dm for white cards on mention "cards"
                print mention
                if not datetime.datetime.strptime(str(mention.created_at), '%Y-%m-%d %H:%M:%S') > lastBlackTweetTime or\
                        mention.user.screen_name in sentCards:
                    continue
                if re.search("cards", mention.text, flags=re.IGNORECASE):
                    whiteCardsDM = "; ".join(pick_white_cards(whiteCards))
                    #print "white cards: " + str(whiteCardsDM.__len__()) + " " + whiteCardsDM
                    sentCards.append(mention.user.screen_name)
                    send_direct_message(mention.user.screen_name, whiteCardsDM)
                    print "Sent cards to @" + mention.user.screen_name

        if i >= waitTime:
            print "Done waiting.  Searching for a winner"
            answers = []
            highScore = 0
            user = ""
            mentions = get_mentions(1200)
            print "Total Mentions found: %s" % (len(mentions))

            for mention in mentions:
                if mention.in_reply_to_status_id != blackCardID:
                    continue
                score = mention.favorite_count + mention.retweet_count
                answers = mention.text.replace(twitterHandle, "").split(";")
                if not len(answers) == neededAnswers:
                    continue

                if score >= highScore:
                    user = str(mention.user.screen_name)
                    highScore = score

            if not user:
                print "No winner found, Waiting again"
                i = 0
                break

            print "Winner Found %s with a score of %s" % (user, highScore)
            #replace - with the user's answers
            #remove(pick 2/3)
            currentBlackCard = currentBlackCard.replace("(Pick 2) ", "").replace("(Pick 3) ", "")
            if re.search("-", currentBlackCard):
                for answer in answers:
                    currentBlackCard = currentBlackCard.replace("-", answer.strip(), 1)
            else:
                for answer in answers:
                    currentBlackCard = currentBlackCard + " " + answer

            #mention the winning user
            print "The winning tweet: " + currentBlackCard
            update_status("%s@%s" % (currentBlackCard, user))
            print "Total Round Length: " + str(datetime.datetime.now() - lastBlackTweetTime)
            waiting = False

        #wait 11 seconds
        print "Sleeping.  Waiting %s cycles (%s seconds)" % (waitTime-i, sleepTime * (waitTime-i))
        time.sleep(sleepTime)
        i += 1

if __name__ == '__main__':
    main()
