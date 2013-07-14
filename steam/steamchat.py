import steam

SID = steam.SteamID

class steamModule:
	def __init__(self):
		self.friends = steam.getclientfriends()
		self.user    = steam.getclientuser()
		self.callbacks = {}
		self.sendBuffer = b""
	def recvCallback(self):
		success, num, data = steam.getcallback()
		if success:
			if num in self.callbacks:
				if data:
					self.callbacks[num](self,*data)
				else:
					print("callback: "+str(num)+" returned None data")
			else:
				print("ignored callback: "+str(num))
			steam.freecallback()
		return success
	def getChatMessage(self, chatID, messageID):
		return self.friends.GetChatMessage(chatID, messageID)
	def getFriendMessage(self, userID, messageID):
		return self.friends.GetFriendMessage(userID, messageID)
	def addHandler(self, callbackID, handler):
		self.callbacks[callbackID] = handler
	def clearHandlers(self):
		self.callbacks = {}
	def getMyName(self):
		return self.friends.GetPersonaName()
	def setMyName(self, name):
		self.friends.SetPersonaName(name)
	def getTheirName(self, steamID):
		return self.friends.GetFriendPersonaName(steamID)
	def getChatName(self, chatID):
		return self.friends.GetChatName(chatID)
	def getChatMemberCount(self, chatID):
		return self.friends.GetChatMemberCount(chatID)
	def getChatMemberByIndex(self, chatID, index):
		return self.friends.GetChatMemberByIndex(chatID, index)
	def getChatMembers(self, chatID):
		count = self.friends.GetChatMemberCount(chatID)
		name = ""
		for i in range(count):
			name += self.friends.GetFriendPersonaName(self.friends.GetChatMemberByIndex(chatID, i)) + ", "
		return name[:-2]
	def sendChatMessage(self, chatID, message):
		if not self.friends.SendChatMessage(chatID, message):
			print("Send failed")
	def sendFriendMessage(self, userID, message):
		if not self.friends.SendFriendMessage(userID, message):
			print("Send failed")
	def sendChatEmote(self, chatID, emote):
		self.sendChatMessage(chatID, emote)
		return
		
		if not self.friends.SendChatEmote(chatID, emote):
			print("Send failed")
	def getSteamID(self):
		return self.user.GetSteamID()