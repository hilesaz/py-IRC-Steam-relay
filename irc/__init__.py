import socket
import select
import log
from irc.irc_numeric_names import numerictoname
from command_handler import CommandHandler

logger = log.Logger(__name__)


SM__IRC_BUFFER_SIZE = 512
SM__CONNECT_TIMEOUT = 3

def deUni(str):
	return str.encode("ASCII","replace").decode("ASCII")
	
	
class IRCUser:
	#used as either IRCUser(identifier[, password]) or 
	#IRCUser(nick[, user][, password])
	def __init__(self, nick=None, user=None, password=None, hostName=None, hostMask=None):
		self.password = password
		self.nick, self.user, self.hostName = IRCUser.parseIdentifier(hostMask) if hostMask else nick, user, hostName
		if not self.nick:
			raise TypeError("IRCUser needs either nick or valid identifier")
			
	def parseHostMask(hostMask):
		nicksplit = hostMask.split('!')
	
class IRCModule:
	
	def __init__(self, servers, channels, name, password = ""):
		self.s = {}#IRC socket
		self.commandHandler = CommandHandler(self)
		self.user = name[0]#user
		self.nick = name[1]#nick
		self.readBuffer = ""#leftover from last block for partial IRC messages
		self.sendBuffer = b""
		self.serverList = servers
		self.channels = channels
		self.users = {}
		self.password = password
			
	def connect(self, host=None):
		self._connect(host if host else servers[0])
	
	def reconnect(self, host = None):
		if host == None:
			for server in self.serverList:
				if self.reconnect(server):
					return True
			logger.warning("Reconnect failed")
			return False
		else:
			logger.info("Reconnecting to",host)
			return self._connect(host)
		
	def _connect(self, host):
		try:
			self.s = socket.create_connection(host, SM__CONNECT_TIMEOUT)
		except socket.gaierror as err:
			logger.warning("Failed to resolve hostname:",host)
			return False
		except socket.timeout as err:
			logger.warning("Timed out connecting to IRC:",host)
			return False
		except OSError as err:
			logger.debug(err)
			return False
		self.s.setblocking(0)
		
		def _quitScrap(self, *args):
			pass
		self.commandHandler.add("QUIT", _quitScrap)
		def _nickScrap(self, *args):
			pass
		self.commandHandler.add("NICK", _nickScrap)
		def _partScrap(self, *args):
			pass
		self.commandHandler.add("PART", _partScrap)
		def _joinScrap(self, *args):
			pass
		self.commandHandler.add("JOIN", _joinScrap)
		def _kickScrap(self, *args):
			pass
		self.commandHandler.add("KICK", _kickScrap)
		def _onPing(self, prefix, server1, server2 = ""):
			self.sendCommand("PONG :"+server1)
		self.commandHandler.add("PING", _onPing)
		
		def _joinScrap(self, *args):
			self.joinChannels()
			self.commandHandler.removeTagged("joinChannels")
		self.commandHandler.addTagged("001", _joinScrap, "joinChannels")
		if False:#add ghosting support later
			def _ghostScrap(self, *args):
				pass
			self.commandHandler.addTagged("433", _ghostScrap, "joinChannels")
		if self.password != "":
			self.sendCommand("PASS "+self.password)
		self.sendCommand("NICK "+self.nick)
		self.sendCommand("USER "+self.user+" 0 * :me")
		return True
	
	def disconnect(self, reason = "Because reasons."):
		self.commandHandler.reset()
		self.sendCommand("QUIT :"+reason)
		self.s.shutdown(1)#change to 3?
		self.s.close()
		self.s = {}
		
	def prepareNameQuery(self, channel):
		self.users[channel.upper()] = []
		handlerTag = "join "+channel
		def _getNames(self, prefix, me, equals, _channel, names):
			if channel.upper() == _channel.upper():
				self.users[channel.upper()].append(names.split())
		def _endNames(self, *args):
			self.commandHandler.removeTagged(handlerTag)
		self.commandHandler.addTagged("343", _getNames, handlerTag)
		self.commandHandler.addTagged("366", _endNames, handlerTag)

	def joinChannels(self):
		for channel in self.channels:
			self.prepareNameQuery(channel)
			self.sendCommand("JOIN "+channel)
			
	def sendCommand(self, command):
		if not self.s:
			logger.debug("tried to send command:",command,"to disconnected bot")
			return False
		[], writeable, [] = select.select([],[self.s],[],0)
		if len(writeable) == 0:
			logger.warning("sock couldn't be opened for writing")
			logger.debug("message lost: "+command)
		else:
			for sock in writeable:#This would need to be fixed for multiple IRC clients
				toSend = (command+"\r\n").encode("UTF-8","replace")
				if len(toSend) != self.s.send(toSend):
					logger.debug("Long message implicitly trimmed")
		
	def sendMessage(self, channel, message):
		#print(len(message),deUni(message))
		while len(message) > 0:
			chunkSize = min(400,len(message));
			self.sendCommand("PRIVMSG "+channel+" :"+message[:chunkSize])
			message = message[chunkSize:]
		
	#returns false on bad socket
	def recvCommand(self):
		if not self.s:
			logger.debug("tried to poll disconnected bot")
			return False
		readable,[],errors = select.select([self.s],[],[self.s],0)
		if len(errors) != 0:
			logger.debug("socket error")
			self.reconnect()
		if len(readable) != 0:
			try:
				data = self.s.recv(SM__IRC_BUFFER_SIZE).decode("UTF-8","replace")
			except:
				return False
			if len(data) == 0:
				return False
			self.readBuffer += data
			commands = self.readBuffer.split("\r\n")
			for cmd in commands[:-1]:
				self.parseCommand(cmd)
			self.readBuffer = commands[-1]
		return True
			
	def parseCommand(self, command):
		follower = command.find(" :",1)
		if follower != -1:
			splitCommand = command[0:follower].split(" ")
			splitCommand.append(command[follower+2:])
		else:
			splitCommand = command.split(" ")
		prefix = ""
		if splitCommand[0][0] != ":":
			splitCommand.insert(0,"")
		else:
			splitCommand[0] = splitCommand[0][1:]
		key = splitCommand.pop(1)
		if not self.commandHandler.run(key.upper(), *tuple(splitCommand)):
			if key in numerictoname:
				key = numerictoname[key]
