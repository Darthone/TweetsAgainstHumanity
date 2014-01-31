# -*- coding: utf-8 -*-

import tweepy, time, random, re, textwrap, datetime, sys, os 

CONSUMER_KEY = '##KEYS REMOVED##'
CONSUMER_SECRET = '##KEYS REMOVED##' # Make sure access level is Read And Write in the Settings tab
ACCESS_KEY = '##KEYS REMOVED##'
ACCESS_SECRET = '##KEYS REMOVED##'
auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)
api = tweepy.API(auth)

blackCardsFile=open('blackcards.txt','r')
blackCardsLines=blackCardsFile.readlines()
blackCardsFile.close()

whiteCardsFile=open('whitecards.txt','r')
whiteCardsLines=whiteCardsFile.readlines()
whiteCardsFile.close()

blackCards = []
whiteCards = []
printed = []
pickedWhite = []
sentCards = []
waiting = False
tryingApi = True

startDate = datetime.datetime.now()
apiTime = datetime.datetime.now()
rulesString = 'Tweet "cards" at me for white cards. Reply to my Black Card Tweet with a response. The Tweet with the most favorites + retweets wins! '
twitterHandle = "@TweetsVH"
waitTime = 240 #cycles
sleepTime = 30 #seconds
tryTime = 120 #seconds
i = 0
ruleTweet = 5
ruleCount = 0
apiCount = 0

def loadBlackCards():
	for line in blackCardsLines:
		blackCards.append(line)

def loadWhiteCards():
	for line in whiteCardsLines:
		whiteCards.append(line)

def pickWhiteCards():
	thisPickedWhite = None
	thisPickedWhite = random.sample(whiteCards, 7)
	return thisPickedWhite

def generateUID():
	UID = str(os.urandom(1))
	return UID
	
#read white cards in
print "Loaded White Cards"
loadWhiteCards()

while 1==1:
	if not waiting:
		i=0
		#tweet black card
		if not blackCards:
			loadBlackCards()
			print "Loaded Black Cards"
		
		#trim
		print "Picking Black Card"
		currentBlackCard = random.choice(blackCards)
		currentBlackCard = currentBlackCard.replace("Draw 2, ", "")
		CurrentBlackCard = "BLACK CARD: " + currentBlackCard
		#post Cards
		tryingApi = True
		while tryingApi:
			try:
				api.update_status(currentBlackCard)
				tryingApi=False
			except Exception,e: 
				print "Unexpected error. Trying Again: " + str(e)
				time.sleep(tryTime)
				continue
				
		tryingApi = True
		while tryingApi:
			try:
				blackCardID = (api.home_timeline())[0].id
				tryingApi=False
			except Exception,e: 
				print "Unexpected error. Trying Again: " + str(e)
				time.sleep(tryTime)
				continue
		
		apiCount+=2
		if re.search("pick",currentBlackCard, flags=re.IGNORECASE):
			tryingApi = True
			while tryingApi:
				try:
					api.update_status('Remember to separate your responses with a semicolon(;) ' + generateUID())
					tryingApi=False
				except Exception,e: 
					print "Unexpected error. Trying Again: " + str(e)
					time.sleep(tryTime)
					continue
			
			neededAnswers = int(currentBlackCard[6:7])
			print "Answers Needed: " + str(neededAnswers)
		else:
			neededAnswers = 1
			print "Answers Needed: " + str(neededAnswers)
		print currentBlackCard
		blackCards.remove(currentBlackCard)
		lastBlackTweetTime = datetime.datetime.now()
		sentCards = None
		sentCards = []
		waiting = True
		winnerFound = False
		
		if ruleCount == 0:
			tryingApi = True
			while tryingApi:
				try:
					api.update_status(rulesString + generateUID())
					tryingApi=False
				except Exception,e: 
					print "Unexpected error. Trying Again: " + str(e)
					time.sleep(tryTime)
					continue
			apiCount+=1
			ruleCount = ruleTweet
			print "Tweeted Rules"
		ruleCount-=1	
		
	if waiting:
		print "Checking for card requests in all mentions"
		#check for card requests
		tryingApi = True
		while tryingApi:
			try:
				mentions  = api.mentions_timeline(count=50)
				tryingApi=False
			except Exception,e: 
				print "Unexpected error. Trying Again: " + str(e)
				time.sleep(tryTime)
				continue
		apiCount+=1
		for mention in mentions:
			#print mention.user.screen_name + ": " + mention.text
			#send out dm for white cards on mention "cards"
			if not datetime.datetime.strptime(str(mention.created_at), '%Y-%m-%d %H:%M:%S') > lastBlackTweetTime: continue
			if mention.user.screen_name in sentCards:continue
			if re.search("cards", mention.text, flags=re.IGNORECASE):
				#pick white cards
				pickedWhite = None
				pickedWhite = []
				pickedWhite = pickWhiteCards()
				whiteCardsDM = ""
				for card in pickedWhite:
					card = card.strip()
					if card.endswith("."): card = card[:-1]
					whiteCardsDM = whiteCardsDM + card + "; " 
					
				if whiteCardsDM.__len__() > 140:
					messages = textwrap.wrap(whiteCardsDM, 140)
				else:
					messages = None
					messages = []
					messages.append(whiteCardsDM)
		
				#print "white cards: " + str(whiteCardsDM.__len__()) + " " + whiteCardsDM	
				sentCards.append(mention.user.screen_name)
				print "Sending cards to @" + mention.user.screen_name
				for message in messages:
					tryingApi = True
					while tryingApi:
						try:
							api.send_direct_message(user=mention.user.screen_name,text=message)
							tryingApi=False
						except Exception,e: 
							print "Unexpected error. Trying Again: " + str(e)
							time.sleep(tryTime)
							continue
					apiCount+=1	

	if i == waitTime:
		print "Done waiting.  Searching for a winner"
		answers = []
		highScore = 0
		user = ""
		tryingApi = True
		while tryingApi:
			try:
				mentions  = api.mentions_timeline(count=1200)
				tryingApi=False
			except Exception,e: 
				print "Unexpected error. Trying Again: " + str(e)
				time.sleep(tryTime)
				continue
		apiCount+=1
		
		print "Total Mentions found: " + str(len(mentions))

		for mention in mentions:
			if not mention.in_reply_to_status_id == blackCardID: continue
			score = mention.favorite_count + mention.retweet_count
			answers = (mention.text.replace(twitterHandle, "").split(";"))
			if isinstance(answers,list):
				numberAnswers = len(answers)	
			else:
				numberAnswers = 1
			if not numberAnswers == neededAnswers: continue
			if score >= highScore:
				user = str(mention.user.screen_name)
				highScore = score				
				#else:
				#	tryingApi = True
				#	while tryingApi:
				#		try:
				#			api.send_direct_message(user=mention.user.screen_name,text="You won, but your Tweet was in an improper format.")
				#			tryingApi=False
				#		except Exception,e: 
				#			print "Unexpected error. Trying Again: " + str(e)
				#			time.sleep(tryTime)
				#			continue
				#	apiCount+=1
					#message user saying improper format
		if user == "":
			print "No winner found, Waiting again"
			i =0
			break
		print "Winner Found %s with a score of %s" % (user,highScore)
		#replace - with the user's answers
		#remove(pick 2/3)
		currentBlackCard = currentBlackCard.replace("(Pick 2) ","").replace("(Pick 3) ","")
		if re.search("-",currentBlackCard):
			for answer in answers:
				currentBlackCard = currentBlackCard.replace("-", answer.strip(), 1)
		else:
			for answer in answers:
				currentBlackCard = currentBlackCard + " " + answer
		print "The winning tweet: " + currentBlackCard
		#mention the user
		currentBlackCard = currentBlackCard + "@" + user
		
		#split the tweet if needed
		if currentBlackCard.__len__() > 140:
			tweets = textwrap.wrap(currentBlackCard, 140)
		else:
			tweets = None
			tweets = []
			tweets.append(currentBlackCard)
	
		#announce winner
		for tweet in tweets:
			tryingApi = True
			while tryingApi:
				try:
					api.update_status(tweet)
					tryingApi=False
				except Exception,e: 
					print "Unexpected error. Trying Again: " + str(e)
					time.sleep(tryTime)
					continue
			apiCount+=1
		print "Posted Winning Tweet"
		print "Total Round Length: " + str(datetime.datetime.now() - lastBlackTweetTime)
		waiting = False
		
	
	if apiTime < datetime.datetime.now()-(datetime.timedelta(hours = 1)):
		apiTime = datetime.datetime.now()
		print "Api Timer refresh"
		apiCount = 0
	
	
	#wait 11 seconds
	print "Sleeping.  Waiting " + str(waitTime-i) + " cycles (" + str(sleepTime * (waitTime-i)) + " seconds)"
	print "Current API Calls Count: " + str(apiCount)
	time.sleep(sleepTime) # Sleep for 1 hour = 3600
	i+=1