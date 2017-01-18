from pyflock import FlockClient, verify_event_token
# You probably want to copy this entire line
from pyflock import Message, SendAs, Attachment, Views, WidgetView, HtmlView, ImageView, Image, Download, Button, OpenWidgetAction, OpenBrowserAction, SendToAppAction

app_id = '6dd7e4b0-3340-4a4f-9243-e47cb8da8ee1'
app_secret = '31f84344-5bf6-4e37-9f66-06039b523702'

#Create a flock client. Needs token and app id for this. You can get the token id and app id when you register. This is for a bot.
#flock_client = FlockClient(token=app_secret, app_id=app_id)

import webapp2
import json
import datetime 
from time import gmtime, strftime
import logging
logging.basicConfig(level=logging.INFO) # dev_appserver.py --log_level debug .
log = logging.getLogger(__name__)

APP_TOKEN = "X-Flock-Event-Token"
USERSFILE = "flockusers.json"
#Test 
#APPID = "8cbf9096-4a7f-4f25-98e4-83bb29db8ee8"
#APPSECRET = "d8566d25-a2a0-4e78-ab33-f90dc7c27584"

#MinutesOfMeeting
APPID = "465d5715-4ad8-4803-b15d-ffcd3f22e0ee"
APPSECRET = "136ea469-542a-45fb-aff2-fb014e3e2936"
APPUSERS = {}
CURRENTMEETING = None

#Main Flock app management class
class FlockHandler(object):

	def __init__(self, appId, appSecret):
		self.appId = appId
		self.appSecret = appSecret
		self.appusers = {} #Valid users
		self.mom = None #Current meeting
		self.loadUsers()

#Create client for current user in current App - from Flock SDK
	def flockClient(self):
		self.flock_client = FlockClient(token=self.getUserToken(self.user), app_id=self.appId)
		return self.flock_client
		
#Get client for current user
	def getClient(self,headers,user):
		self.getToken(headers)
		self.user = user
		return self.flockClient()
	
#User Management - userID's ans associated tokens held in local USERSFILE
	def loadUsers(self):
		with open(USERSFILE) as fp:
			self.appusers = json.load(fp)
		log.info("User count: %s" % len(self.appusers))

	def saveUsers(self):
		with open(USERSFILE, 'w') as fp:
			json.dump(self.appusers, fp)
		log.info("User count: %s" % len(self.appusers))
			
	def addUser(self,user,token):
		log.info("addUser(%s,%s)" % (user,token))
		self.appusers[user] = token
		self.saveUsers()

	def delUser(self,user):
		log.info("delUser(%s)" % user)
		self.appusers.pop(user,None)
		self.saveUsers()

	def getUserToken(self,user):
		return self.appusers[user]
######

	def checkAppId(self,id):
		if id == self.appID:
			return True
		return False
		
#Extract application token from request headers
	def getToken(self,headers):
		self.token = headers.get(APP_TOKEN)
		#log.info("%s: %s" % (APP_TOKEN,self.token))
		return self.token
				
#Install: Add current user to users list
	def appInstall(self,data):
		log.info("appInstall: %s" % data)
		user = data['userId']
		self.token = data['token']
		self.addUser(user,self.token)
		log.info("user: %s" % user)
		log.info("token: %s" % self.token)
		return True
		
	def appUninstall(self,data):
		log.info("appUninstall: %s" % data)
		log.info("user: %s" % data['userId'])
		self.delUser(data['userId'])
		return True

#Manage slash commands (/mom) from app:
#   start: Create new session (close previously open)
#   stop: Close session
#   list: List captured minutes
#   default save as a minute
#Repond with a message to current groupchat 
#True return = success
	def slashCommand(self,data):
		ret = False
		command = data['command']
		log.info("slashCommand: %s" % command)
		if command == "mom":
			text = data.get('text')
			msg = None
			if text and len(text):
				text = text.strip()
				if not self.mom and not text.startswith("start"):
					log.info("mom %s" % self.mom)
					msg = Message(to=data['chat'],text="No meeting in progress!\n Use: /mom start meeting_name")
				elif text.startswith("start"):
					if self.mom:
						self.mom.close()
					self.mom = Mom(text[5:])
					msg = Message(to=data['chat'],text="Started Meeting '%s' at %s" % (self.mom.name,strftime("%H:%M:%S",self.mom.start)))
				elif text.startswith("stop"):
					if self.mom:
						msg = Message(to=data['chat'],text="Stopping Meeting '%s'" % self.mom.name)
						self.mom.close()
						self.mom = None
					else:
						msg = Message(to=data['chat'],text="No meeting in progress")
				elif text.startswith("list"):
					list = "Meeting %s (started at %s)\n" % (self.mom.name,strftime("%H:%M:%S",self.mom.start))
					list += self.mom.list()
					msg = Message(to=data['chat'],text=list)
				else:
					add = self.mom.add(text)
					msg = Message(to=data['chat'],text=add.formatted())
					
			if msg:
				res = self.flock_client.send_chat(msg)
			ret = True		
		return ret
		
#Populate side widget for open meeting
	def momWidgetShow(self,data):
		log.info("momWidgetShow()")
		if not self.mom:
			return "<h3>No Meeting in progress</h3>"
		
		return self.mom.show()
			
FLOCK = FlockHandler(APPID,APPSECRET)
			
#A Meeting
#TODO use client local time
class Mom():
	
	def __init__(self,name):
		self.minutes = []
		self.start = gmtime()
		self.name = name.strip()
		self.widget = None

	def close(self):
		pass
	
#Add minute
	def add(self,text):
		min = Minute(text)
		self.minutes.append(min)
		return min
		
#Create text list of formatted minutes
	def list(self,sep='\n'):
		ret = ""
		for m in self.minutes:
			ret += m.formatted() 
			ret += sep
		return ret
	
#Create/show side widget
	def show(self):
		if not self.widget:
			self.widget = momWidget(self)
		return self.widget.show()
		
#An individual minute entry - timestamped
class Minute():
	def __init__(self,text):
		self.text = text
		self.time = gmtime()
		
#Format minute with a timestamp
	def formatted(self):
		return "%s: %s" % (strftime("%H:%M:%S",self.time),self.text)
		
		
		
#Side widget formatter
#TODO Updates
class momWidget():
	
	def __init__(self,meeting):
		self.mom = meeting
		
	def show(self):
		return self.showPage(self.mom.list(sep='<br/>'))
		
	def showPage(self,conts):
		PAGE = """
		<html>
				<body>
				<h3>Minutes for Meeting %s</h3>
				<h4>Started at %s</h4>
				%s
				</body>
		</html>""" % (self.mom.name,strftime("%H:%M:%S",self.mom.start),conts)
		return PAGE
		
	
		
#Http request/response handler
class FlockWebapp2(webapp2.RequestHandler):

#POST requests
	def post(self,node):
		log.info("post(%s)" % node)
		success = False

		if node == "events":
			success = self.handleEvents()
		
		return self.respond(success)
		
#GET requests
	def get(self,node):
		log.info("get(%s)" % node)

		if node == "welcome":
			success =  self.welcome()
		else:
			event = self.request.get('flockEvent')
			if event:
				eventData = json.loads(event)
				userId = eventData.get('userId')
				log.info("userId: %s" % userId)
				self.setupFlock(userId)
				success = False
		
				if node == "momview":
					success = self.momView(eventData)
		
		return self.respond(success)
	
	def setupFlock(self,user):
		self.client = FLOCK.getClient(self.request.headers,user)
		log.info("Client: %s" % self.client)

#Response creator - False success = http error
	def respond(self,success):
		log.info("respond %s" % success)
		if success:
			self.response.set_status(200,"OK")
		else:
			self.error(404)
			self.response.out.write('<h3>404 Not Found.</h3><p><br/>Page not found.</p>')
			

#Acknowledge install
	def welcome(self):
			self.response.out.write('<h2>Welcome to the Dataliberate Minutes App!.</h2>')
			return True
	
#Handle sidewidget
	def momView(self,data):
		log.info("momView()")
		content = FLOCK.momWidgetShow(data)
		if not content:
			return False
		if len(content):
			self.response.out.write(content)
		
		return True

#Handle slash events
	def handleEvents(self):
		log.info("handleEvents()")
		eventData = json.loads(self.request.body)
		user = eventData['userId']
		event = eventData['name']
		log.info("Event Name: %s" % event)
		
		ret = False
		if event == "app.install":
			ret = FLOCK.appInstall(eventData)
		elif event == "app.uninstall":
			ret = FLOCK.appUninstall(eventData)
		elif event == "client.slashCommand":
			self.setupFlock(user)
			ret = FLOCK.slashCommand(eventData)
		
		return ret

#Create Webapp 
app = webapp2.WSGIApplication([ ('/(.*)', FlockWebapp2), ], debug=True)

def main():
	from paste import httpserver
	#httpserver.serve(app, host='172.31.33.21', port='80')
	httpserver.serve(app, host='127.0.0.1', port='80')

if __name__ == '__main__':
	main()
