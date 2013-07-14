from Crypto.Cipher import AES
from Crypto import Random
from Crypto.Random import random
import socket
import struct

from command_handler import CommandHandler
from steam_servers import servers

def encryptData(key, data):
	iv = Random.new().read(AES.block_size)
	ECBCipher = AES.new(key, AES.MODE_ECB, "")
	
	CBCCipher = AES.new(key, AES_MODE_CBC, iv)
	
	return ECBCipher.encrypt(iv) + CBCCipher.encrypt(data)
	
def decryptData(key, data):
	hashedIV = data[:16]
	data = data[16:]
	
	ECBCipher = AES.new(key, AES_MODE_ECB, "")
	iv = AES.decrypt(hashedIV)
	
	CBCCipher = AES.new(key, AES_MODE_CBC, iv)
	
	return CBCCipher.decrypt(data)
	
class SteamConnection:
	def __init__(self, server, sessionKey=None):
		self.sessionKey = sessionKey
		self.socket = {}
		self.dataSize = 0
		
		self.connect(server)
	
	def connect(self, server):
		self.socket = socket.create_connection(server)
		
	def send(self, data):
		#sessionKey is set when Steam decides to start encrypting.
		#All packets before aren't encrypted and all afterwards are.
		if self.sessionKey:
			data = encryptData(self.sessionKey, data)
			
		self.socket.send(struct.pack("<IIs", len(data), SteamConnection.MAGIC, data))
		
	#returns False on partial packet, the data on completion
	def recv(self):
		if not self.dataSize:
			hdr = fullRecv(8)
			self.dataSize, magic = struct.unpack("<II", hdr)
			if magic != SteamConnection.MAGIC:
				raise IOError("Bad message received")
		data = self.fullRecv(self.dataSize)
		self.dataSize = 0
		if self.sessionKey:
			data = decryptData(self.sessionKey, data)
		return data
	
	#must not be called for different recv until returns data
	def fullRecv(self, size):
		if not self.partialPacketSize:
			self.partialPacketSize = size
			self.packetData = b''
		data = self.socket.recv(self.partialPacketSize)
		self.partialPacketSize -= len(data)
		self.packetData += data
		
		if self.partialPacketSize:
			raise SteamConnection.PartialMessageError
		return self.packetData
		
	class PartialMessageError(IOError):
		pass
	MAGIC = "VT01"
		
class SteamID:
	pass
	
class SteamClient:
	def __init__(self, username, password, code, hash=None):
		self.username = username
		self.password = password
		self.code = code
		self.hash = hash
		
		self.outstandingJobs = []
		self.currentJobID = 0
		
		self.steamID = SteamID(Inst=1, Uni=SteamID.Public, type=SteamID.Inviv)
		
		self.sessionID = 0
		
		self.handler = CommandHandler()
		
		self.connection = {}
		self.connect(random.choice(servers))
		
	def connect(self, server):
		self.connection = SteamConnection(server)
		
