from irc import IRCModule
import log

logger = log.Logger(__name__)

servers = ["localhost"]
channels = ["#bovine"]
names = ["bovMaster","bov1","bov2","bov3","bov4","bov5","bov6"]

clients = [IRCModule(servers, channels, ("bov_bot",nick), password="HAHA") for nick in names]

def _onTest(self, *args):
	logger.debug(args)
	channel = args[1]
	message = args[2]
	if message == "!test" and channel == "#bovine":
		self.sendMessage(channel, "I guess I work, sort of")
		
def _hookExit(self, *args):
	message = args[2]
	if message == "!exit":
		self.disconnect()

clients[0].commandHandler.add("PRIVMSG", _onTest)

for client in clients:
	client.commandHandler.add("PRIVMSG", _hookExit)
	client.connect(servers[0])

while len(clients) > 0:
	for client in clients:
		if not client.recvCommand():
			clients.remove(client)
			logger.error("client: %s broke",client.nick)