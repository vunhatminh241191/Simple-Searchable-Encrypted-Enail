#!/usr/bin/env python
 
LISTEN_PORT = 1431
SERVER_PORT = 143
SERVER_ADDR = "localhost"
 
from twisted.internet import protocol, reactor
from email.parser import Parser
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
import email, imaplib, re, StringIO, ConfigParser, base64
from encryption import *

header_part = ['From', 'To', 'Subject']

class ServerProtocol(protocol.Protocol):
	
	# Using self.client to connect Client-Proxy
	# Using self.other to get other function class
	# Using self.email_address to get the whole user's email_address 
	# Using self.flag to know which data we need
	Tokenize_append = "APPEND"
	Tokenize_Login = "LOGIN"
	Tokenize_authenticate = "authenticate plain"

	def __init__(self):
		self.client = None
		#self.other = Other_Function()
		self.email_address = None
		self.buffer = None
		self.flag_Login = False
		self.flag_Append = False

	# Create a connection between the first part and the second part of proxy
	def connectionMade(self, line):
		print repr(line)
		factory = protocol.ClientFactory()
		factory.protocol = ClientProtocol
		factory.server = self
		reactor.connectTCP(SERVER_ADDR, SERVER_PORT, factory)

	# The gate Client sending data to Proxy
	def dataReceived(self, data):
		print "C->S: %s", repr(data)

		if self.client:
			# login function
			if self.Tokenize_authenticate or self.Tokenize_authenticate.upper() in data:
				# Open the flag to get the new message
				self.flag_Login = True
			elif self.flag_Login == True:
				# Using base64 to decrypt information
				self.email_address = base64.b64decode(
					data.replace('\r\n','')).split('\x00')[1] + '@' + SERVER_ADDR
				self.flag_Login = False
			elif self.Tokenize_Login or self.Tokenize_Login.lower() in data and len(
				data.split(' ')) == 4:
				# Some Email clients do not encrypted string, solving easily
				self.email_address = data.split(' ')[-1] + '@' + SERVER_ADDR

			# Appeding data to mail box
			if self.Tokenize_append or self.Tokenize_append.lower() in data:
				self.flag_Append = True
				self.buffer += data
				return
			# Waiting more data until see "\r\n"
			elif self.flag_Append == True:
				if len(data) == 2:
					self.flag_Append = False
					self.buffer += data
					transfer_email = self.other.Append(self.buffer)
				else:
					self.buffer += data
					return
			self.client.write(data)
		else:
			self.buffer = data

	# The gate Proxy sending data to Client
	def write(self, data):
		print "S->C: %s", repr(data)

		'''if "FETCH" and "OK Fetch completed" and "BODY[]" in data:
			data = self.other.Fetch(data, self.cipher_key)
		elif "FETCH" and "RFC822.SIZE" in data:
			print "hehehe"
			data = self.other.Preview(data, self.cipher_key)'''

		self.transport.write(data)

	def sending_append(self, append_cmd, transfer_email):
		for i in range(3):
			if i == 0:
				self.client.write(append_cmd)
			elif i == 1:
				self.client.write(transfer_email)
			else:
				self.client.write('\r\n')
		return

class ServerFactory(protocol.ServerFactory)

class ClientProtocol(protocol.Protocol):
	def connectionMade(self):
		self.factory.server.client = self
		self.write(self.factory.server.buffer)
		self.factory.server.buffer = ''
 
	# Server => Proxy
	def dataReceived(self, data):
		self.factory.server.write(data)
 
	# Proxy => Server
	def write(self, data):
		if data:
			self.transport.write(data)

'''class Other_Function:
	def __init__(self):'''


def main():
	factory = protocol.ServerFactory()
	factory.protocol = ServerProtocol

	reactor.listenTCP(LISTEN_PORT, factory)
	reactor.run()
if __name__ == '__main__':
	main()