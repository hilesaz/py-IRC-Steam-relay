import weakref

#an endpoint has:

#a link is a (endpoint,endpoint) tuple

class ListWeakRefTarget(list):
	pass

class Relay:
	def __init__(self):
		self.links = []
	def addLink(self, link):
		WRLink = ListWeakRefTarget(link)
		for endpoint in WRLink:
			endpoint.link = weakref.proxy(WRLink)
		self.links.append(WRLink)