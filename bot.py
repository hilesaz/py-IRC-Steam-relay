import irc
import steamchat
import time
import re
import random
import os
import sys
import log

logger = log.Logger(__name__)

SM__IRC_NICKSERV_PASS = "myBotPassword"

servers = ["localhost"]
channels = ["#mlas1","#bovine"]
rejoinCode = "P6-9ACXR8HN_-7G6"
botIrcNick = "S"

def invertDict(dict):
	return {v:k for k,v in dict.items()}
#IRCtoSteam = {"#MLAS1": steamchat.SID("110338190873547250"), "#bovine": steamchat.SID("110338190873901486")}
IRCtoSteam = {"#bovine":steamchat.SID("110338190875167146")}
SteamtoIRC = invertDict(IRCtoSteam)
if invertDict(SteamtoIRC) != IRCtoSteam:
	raise ValueError("IRCtoSteam links must be invertable (unique channels on both sides)")


def isIRCMeNick(nick):
	return nick == botIrcNick
def isIRCMe(user):
	return user == "bov_pybot1"
	
def IRCEscapeName(name):#used to make steam names look like IRC names
	return re.sub("[^a-zA-Z0-9\-\[\]\\`^{}_]","",name)
def IRCEscapeMessage(message):#used to make irc messages look ok in steam
	colorOnly = re.sub("[\x02\x1f\x1d\x0f\x16]","",message)
	return re.sub("\x03\d?\d?(?:,\d\d?)?","",colorOnly)
	
def parseIRCUserString(userString):
	excl = userString.find('!')
	at   = userString.find('@')
	if excl == -1 or at == -1 or at < excl:
		return ("","")
	return (userString[:excl],userString[excl+1:at])

	
def isSteamMe(userID):
	return userID == steam.getSteamID()
	
steamAdmins = {steamchat.SID("STEAM_0:0:26259933"):True,steamchat.SID("STEAM_0:0:6026429"):True,steamchat.SID("STEAM_0:1:41411613"):True,steamchat.SID("STEAM_0:1:2991218"):True}
def isSteamAdmin(userID):
	return userID in steamAdmins


def onGetName(self, prefix, me, equals, channel, names):
	channel = channel.upper()
	if channel in pollingNames:
		pollingNames[channel] = pollingNames[channel]+names
	else:
		printConsole("Got names for channel '"+channel+"' without asking")
		
def onFinName(self, prefix, me, channel, text):
	channel = channel.upper()
	if channel in pollingNames:
		if channel in IRCtoSteam:
			isPrivate, ID = pollingDest[channel]
			if isPrivate:
				steam.sendFriendMessage(ID, "Users on IRC: "+pollingNames[channel].replace(" ",", "))
			else:
				steam.sendChatEmote(ID, "Users on IRC: "+pollingNames[channel].replace(" ",", "))
		else:
			printConsole("Got end of names for unmapped channel: "+channel)
		del pollingDest[channel]
		del pollingNames[channel]
	else:
		printConsole("Got end of names for channel '"+channel+"' without asking")
		
def ListSteamUsers(chatID, userID, command):
	if chatID in IRCtoSteam:
		chat = IRCtoSteam[chatID]
		count = steam.getChatMemberCount(chat)
		IRC.sendMessage(nick, str(count)+" Users on Steam: ")
		for i in range(count):
			ID = steam.getChatMemberByIndex(chat,i)
			if not isSteamMe(ID):
				name = IRCEscapeName(steam.getTheirName(ID))
				if len(name) == 0:
					name = "GABE FUCKING BEAR"
				IRC.sendMessage(nick, name)
				
def ListIRCUsers(chatID, userID, command):
	if chatID in SteamtoIRC:
		channel = SteamtoIRC[chatID]
		pollingNames[channel] = ""
		pollingDest[channel] = (True,userID)
		IRC.addHandlerTagged("353", onGetName, chatID)
		IRC.addHandlerTagged("366", onFinName, chatID)
		IRC.sendCommand("NAMES "+channel)
	
	
botCommands.append(Command("LU",ListIRCUsers,["steam","chat"]))
botCommands.append(Command("LU",ListSteamUsers,["IRC"  ,"chat"]))
	
	
#Commands are put through commandDict to get function to call
def onCommand(self, source, pm, userID, command):
	cmdMatch = command.upper()
	for cmd in botCommands:
		if cmd.matches(source,pm) and cmdMatch.find(cmd.name) == 0:
			if cmd.callback(userID, command[len(cmd.name)+1:]):
				break
				
def onSteamPrivCommand(self, userID, command):
	printConsole([userID, command])
	channel = "#MLAS1"#Must be fixed for multiple channels
	if command.upper().find("LU") == 0:
		if not channel in pollingNames:
			pollingNames[channel] = ""
			pollingDest[channel] = (True,userID)
			IRC.sendCommand("NAMES "+channel)
	elif command.upper().find("CUT") == 0:
		if isSteamAdmin(userID) or isSteamMe(userID):
			steamCut = True
	elif command.upper().find("UNCUT") == 0:
		if isSteamAdmin(userID) or isSteamMe(userID):
			steamCut = False
	elif command.upper().find("ROLL") == 0:
		steam.sendFriendMessage(userID, str(rollDice(command[5:]) or "Invalid roll"))
	elif command.upper().find("PORNI") == 0:
		steam.sendFriendMessage(userID, getPoniLink(command[6:-1]))
	elif command.upper().find("MUTE") == 0:
		if isSteamAdmin(userID) or isSteamMe(userID):
			muted = re.sub("\x00","",command[5:])
			printConsole("\""+muted+"\"")
			muteList[muted] = True
			steam.sendFriendMessage(userID, muted+" was muted")
	elif command.upper().find("UNMUTE") == 0:
		if isSteamAdmin(userID) or isSteamMe(userID):
			muted = re.sub("\x00","",command[7:])
			if muted in muteList:
				del muteList[muted]
				steam.sendFriendMessage(userID, muted+" was unmuted")
	elif command.upper().find("LISTMUTED") == 0:
		for key in muteList:
			steam.sendFriendMessage(userID, key+" is muted")
	elif command.upper().find("KICK") == 0:
		if isSteamAdmin(userID) or isSteamMe(userID):
			IRC.sendCommand("KICK "+channel+" "+command[5:])
	elif command.upper().find("HELP") == 0:
		steam.sendFriendMessage(userID, "Commands are:\n"+
		"LU -> lists users in steam chat\n"+
		"ROLL <count>d<type>+/-<extra> -> rolls up to 100 dice\n"+
		"(PM only) PORNI <tags> -> ponibooru explicit search")
		if isSteamAdmin(userID):
			steam.sendFriendMessage(userID, "Admin commands:\n"+
			"MUTE <username> -> Prevents username's messages from appearing in chat\n"+
			"UNMUTE <username> -> undoes effects of MUTE\n"+
			"LISTMUTED <username> -> Shows a list of all muted usernames")
def onSteamUserCommand(self, chatID, userID, command):
	printConsole([chatID, userID, command])
	if chatID in SteamtoIRC:
		channel = SteamtoIRC[chatID]
		if command.upper().find("LU") == 0:
			if not channel in pollingNames:
				pollingNames[channel] = ""
				pollingDest[channel] = (False,chatID)
				IRC.sendCommand("NAMES "+channel)
		elif command.upper().find("CUT") == 0:
			if isSteamAdmin(userID) or isSteamMe(userID):
				steam.sendChatMessage(chatID, "Link is cut")
				steamCut = True
		elif command.upper().find("UNCUT") == 0:
			if isSteamAdmin(userID) or isSteamMe(userID):
				steam.sendChatMessage(chatID, "Link is uncut")
				steamCut = False
		elif command.upper().find("ROLL") == 0:
			steam.sendChatMessage(chatID, str(rollDice(command[5:])))
		elif command.upper().find("PORNI") == 0:
			steam.sendFriendMessage(userID, getPoniLink(command[6:-1]))
		elif command.upper().find("MUTE") == 0:
			if isSteamAdmin(userID) or isSteamMe(userID):
				muted = re.sub("\x00","",command[5:])
				printConsole("\""+muted+"\"")
				muteList[muted] = True
				steam.sendChatMessage(chatID, muted+" was muted")
				IRC.sendMessage(channel, muted+" was muted")
		elif command.upper().find("UNMUTE") == 0:
			if isSteamAdmin(userID) or isSteamMe(userID):
				muted = re.sub("\x00","",command[7:])
				if muted in muteList:
					del muteList[muted]
					steam.sendChatMessage(chatID, muted+" was unmuted")
					IRC.sendMessage(channel, muted+" was unmuted")
		elif command.upper().find("LISTMUTED") == 0:
			if len(muteList) == 0:
				steam.sendChatMessage(chatID, "No one is muted")
			for key in muteList:
				steam.sendChatMessage(chatID, key+" is muted")
		elif command.upper().find("KICK") == 0:
			if isSteamAdmin(userID) or isSteamMe(userID):
				IRC.sendCommand("KICK "+channel+" "+command[5:])
		else:
			IRC.sendMessage(channel, "!"+command)
def onIRCPrivCommand(self, nick, user, messager, command):
	printConsole(nick,command)
	channel = "#MLAS1"#Must be fixed for multiple channels
	if channel in IRCtoSteam:
		chat = IRCtoSteam[channel]
		if command.upper().find("LU") == 0:
			count = steam.getChatMemberCount(chat)
			IRC.sendCommand("NOTICE "+nick+" Users on Steam: ")
			names = []
			for i in range(count):
				ID = steam.getChatMemberByIndex(chat,i)
				if not isSteamMe(ID):
					names += steam.getTheirName(ID)
			IRC.sendCommand("NOTICE "+nick+" "+IRCEscapeName(", ".join(names)))
		elif command.upper().find("CUT") == 0:
			if nick[0] == "~":
				IRCCut = True
		elif command.upper().find("UNCUT") == 0:
			if nick[0] == "~":
				IRCCut = False
		elif command.upper().find("ROLL") == 0:
			IRC.sendMessage(nick, str(rollDice(command[5:])))
		elif command.upper().find("PORNI") == 0:
			IRC.sendMessage(nick, getPoniLink(command[6:]))
		elif command.upper().find("HELP") == 0:
			IRC.sendCommand("NOTICE "+nick+" Commands are:")
			IRC.sendCommand("NOTICE "+nick+" LU -> lists users in steam chat")
			IRC.sendCommand("NOTICE "+nick+" ROLL <count>d<type>+/-<extra> -> rolls up to 100 dice")
			IRC.sendCommand("NOTICE "+nick+" PORNI <tags> -> ponibooru explicit search")
def onIRCUserCommand(self, nick, user, channel, command):
	channel = channel.upper()
	if channel in IRCtoSteam:
		chat = IRCtoSteam[channel]
		if command.upper().find("LU") == 0:
			count = steam.getChatMemberCount(chat)
			names = []
			for i in range(count):
				ID = steam.getChatMemberByIndex(chat,i)
				if not isSteamMe(ID):
					names.append(steam.getTheirName(ID))
			IRC.sendMessage(channel, str(count - 1) + " Users on Steam: "+", ".join(names))
		elif command.upper().find("CUT") == 0:
			if nick[0] == "~":
				IRCCut = True
		elif command.upper().find("UNCUT") == 0:
			if nick[0] == "~":
				IRCCut = False
		elif command.upper().find("ROLL") == 0:
			IRC.sendMessage(channel, str(rollDice(command[5:])))
		elif command.upper().find("LISTMUTED") == 0:
			if len(muteList) == 0:
				IRC.sendMessage(channel, "No one is muted")
			for key in muteList:
				IRC.sendMessage(channel, key+" is muted")
		elif command.upper().find("PORNI") == 0:
			IRC.sendMessage(channel, getPoniLink(command[6:]))
		else:
			steam.sendChatMessage(chat,"!"+command)

def onSteamPrivMessage(self, friendID, userID, entryType, limited, messageID):
	#if isSteamMe(userID):
	#	return
	printConsole(friendID,userID)
	message = self.getFriendMessage(friendID, messageID)
	printConsole(message)
	if len(message) == 0:
		return
	if entryType == 1 and message[0] == '!':
		onSteamPrivCommand(self, friendID, message[1:])
		
def onSteamChatMessage(self, chatID, userID, entryType, messageID):
	message = self.getChatMessage(chatID, messageID)
	if isSteamMe(userID):
		return
	if len(message) == 0:
		return
	try:
		if entryType == 1 and message[0] == '!':
			onSteamUserCommand(self, chatID, userID, message[1:])
			printConsole(message)
			return
	except IndexError as e:
		printConsole("'",message,"'")
	if IRCCut or steamCut:
		return
	#printConsole(self.friends.GetFriendPersonaName(userID)+" sent "+message)
	if chatID in SteamtoIRC:
		for msg in message.split("\n"):
			if entryType == 1:
				IRC.sendMessage(SteamtoIRC[chatID], "<"+IRCEscapeName(self.friends.GetFriendPersonaName(userID))+"> "+msg)
			elif entryType == 4:
				IRC.sendMessage(SteamtoIRC[chatID], "\01ACTION "+IRCEscapeName(self.friends.GetFriendPersonaName(userID))+" "+msg+"\01")
			else:
				printConsole("Bad entry type: "+str(entryType))
			
def onSteamChatMemberStateChange(self, chatID, userID, changeType, actorID):
	if isSteamMe(userID):
		return
	printConsole(self.friends.GetFriendPersonaName(userID),str(changeType),self.friends.GetFriendPersonaName(actorID))
	if chatID in SteamtoIRC:
		if changeType == 1:
			IRC.sendMessage(SteamtoIRC[chatID], IRCEscapeName(self.friends.GetFriendPersonaName(userID))+" entered chat")
		elif changeType == 4 or changeType == 2:
			IRC.sendMessage(SteamtoIRC[chatID], IRCEscapeName(self.friends.GetFriendPersonaName(userID))+" disconnected from chat")
		elif changeType == 8:
			IRC.sendMessage(SteamtoIRC[chatID], IRCEscapeName(self.friends.GetFriendPersonaName(userID))+" was kicked from chat by "+self.friends.GetFriendPersonaName(actorID))
		elif changeType == 16:
			IRC.sendMessage(SteamtoIRC[chatID], IRCEscapeName(self.friends.GetFriendPersonaName(userID))+" was banned from chat by "+self.friends.GetFriendPersonaName(actorID))
			
			
def onIRCCTCPMessage(self, nick, user, channel, ctcp):
	if ctcp.find("ACTION") == 0:
		steam.sendChatEmote(IRCtoSteam[channel], nick+" "+ctcp[7:])
		
def onPrivateCtcpMessage(self, nick, user, channel, ctcp):
	printConsole("Private CTCP message received from nick ", nick, ": '", ctcp, "'", sep='')
	if ctcp.upper().find(rejoinCode.upper()) == 0:
		rejoinSteam()
		
def rejoinSteam():
	hwnd = win32gui.FindWindowEx(0, 0, 0, "Mylittleandysonic1 Derps - Group Chat")
	if hwnd > 0:
		printConsole("Steam chat found, closing window.")
		win32api.SendMessage(hwnd, win32con.WM_CLOSE, 0, 0)
		
	printConsole("Opening Steam chat.")
	os.startfile("steam://friends/joinchat/103582791432491506")
	
def onIRCChatMessage(self, prefix, channel, message):
	printConsole([channel, prefix, message])
	
	channel = channel.upper()
	nick, user = parseIRCUserString(prefix)
	if isIRCMe(user):
		return
	if nick in muteList:
		return
	message = IRCEscapeMessage(message)
	if len(message) == 0:
		return
	if message[0] == '!':
		if isIRCMeNick(channel):
			onIRCPrivCommand(self, nick, user, channel, message[1:])
		else:
			onIRCUserCommand(self, nick, user, channel, message[1:])
		return
	printConsole(IRCCut,steamCut)
	if IRCCut or steamCut:
		return
	if channel in IRCtoSteam:
		if message[0] == '\x01' and message[-1] == '\x01':
			onIRCCTCPMessage(self, nick, user, channel, message[1:-1])
		else:
			steam.sendChatMessage(IRCtoSteam[channel],nick+": "+message);
	elif isIRCMeNick(channel):
		if message[0] == '\x01' and message[-1] == '\x01':
			onPrivateCtcpMessage(self, nick, user, channel, message[1:-1])
	else:
		printConsole("Not handling message: ", message)
	
def onIRCQuit(self, prefix, message = "Quit"):
	nick, user = parseIRCUserString(prefix)
	if isIRCMe(user):
		return
	channel = "#MLAS1"#THIS IS VERY BAD BUT WE NEED TO STORE USER LISTS OTHERWISE
	if channel in IRCtoSteam:
		steam.sendChatEmote(IRCtoSteam[channel], nick +" left IRC: "+IRCEscapeMessage(message))
def onIRCPart(self, prefix, channel, dunno = None):
	channel = channel.upper()
	nick, user = parseIRCUserString(prefix)
	if isIRCMe(user):
		return
	if dunno:
		printConsole(dunno)
	if channel in IRCtoSteam:
		steam.sendChatEmote(IRCtoSteam[channel], nick +" left IRC")
def onIRCJoin(self, prefix, channel, key = ""):
	channel = channel.upper()
	nick, user = parseIRCUserString(prefix)
	if isIRCMe(user):
		return
	if channel in IRCtoSteam:
		steam.sendChatEmote(IRCtoSteam[channel], nick +" joined IRC")
def onIRCKick(self, prefix, channel, who, comment = ""):
	channel = channel.upper()
	nick, user = parseIRCUserString(prefix)
	if isIRCMeNick(who):
		IRC.sendCommand("JOIN "+channel)
		return
	if channel in IRCtoSteam:
		message = ""
		if comment != "":
			message = ": "+comment
		steam.sendChatEmote(IRCtoSteam[channel], who+" was kicked from chat by "+nick+IRCEscapeMessage(message))
def onIRCNick(self, prefix, newNick):
	nick, user = parseIRCUserString(prefix)
	if nick in muteList:
		del muteList[nick]
		muteList[newNick] = True
	channel = "#MLAS1"
	if channel in IRCtoSteam:
		steam.sendChatEmote(IRCtoSteam[channel], nick+" changed name to "+newNick)
def onIRCNotice(self, prefix, channel, message):
	nick, user = parseIRCUserString(prefix)
	printConsole(nick+message)
def onIRCMode(self, prefix, channel, letters, mask = None, Unknown = None): 
	nick, user = parseIRCUserString(prefix)
	if Unknown != None:
		printConsole(prefix,channel,letters,mask,Unknown)
	if channel in IRCtoSteam:
		steam.sendChatEmote(IRCtoSteam[channel],nick+" set mode "+letters+" "+mask)
	
steam = steamchat.steamModule()

steam.addHandler(steamchat.steam.callback_chatRoomMessage,onSteamChatMessage)
steam.addHandler(steamchat.steam.callback_friendChatMessage,onSteamPrivMessage)
steam.addHandler(steamchat.steam.callback_chatMemberStateChange,onSteamChatMemberStateChange)

IRC = irc.IRCModule(servers=servers, channels=channels, name=("bov_pybot1",botIrcNick))

IRC.addHandler("PRIVMSG", onIRCChatMessage)
IRC.addHandler("QUIT", onIRCQuit)
IRC.addHandler("NICK", onIRCNick)
IRC.addHandler("PART", onIRCPart)
IRC.addHandler("JOIN", onIRCJoin)
IRC.addHandler("KICK", onIRCKick)
IRC.addHandler("NOTICE", onIRCNotice)

running = True
counter = 0
fast = False
try:
	while running:
		try:
			running = IRC.recvCommand()
		except ConnectionError as e:
			steam.sendChatMessage("Bot shut down")
		if fast or not counter % 33:#sequential or three times every second
			fast = steam.recvCallback()
		counter += 1
		time.sleep(0.01)
except BaseException as e:
	printConsole("Bot shut down:", e.message if hasattr(e,"message") else "generic")
	exit(0)
