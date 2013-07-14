
#Untagged handlers are considered to be permanent.
#If you want to ever remove a handler, give it a tag.
class CommandHandler:
	def __init__(self, savedSelf):
		self.savedSelf = savedSelf
		self.commandDict = {}
		self.handlerTags = {}
		
	def add(self, command, fn):
		if command in self.commandDict:
			self.commandDict[command].append(fn)
		else:
			self.commandDict[command] = [fn]
	
	def addTagged(self, command, fn, tag):
		self.add(command, fn)
		taggedFunction = (command, fn)
		if tag in self.handlerTags:
			self.handlerTags[tag].append(taggedFunction)
		else:
			self.handlerTags[tag] = [taggedFunction]
	
	def removeTagged(self, tag):
		if tag in self.handlerTags:
			for taggedCommand in self.handlerTags[tag]:
				self.commandDict[taggedCommand[0]].remove(taggedCommand[1])
			self.handlerTags[tag] = []
	
	#only removes tagged handlers
	def reset(self):
		for tag in self.handlerTags:
			self.removeTagged(tag)
		
	def run(self, command, *args):
		if command in self.commandDict:
			for fn in self.commandDict[command]:
				fn(self.savedSelf, *args)
			return True
		else:
			return False
