import logging
from logging.handlers import TimedRotatingFileHandler

handler = TimedRotatingFileHandler("./logs/bot.log", when="midnight")

def Logger(*args):
	obj = logging.Logger(*args)
	obj.addHandler(handler)
	return obj