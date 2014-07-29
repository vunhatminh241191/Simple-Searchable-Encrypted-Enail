#!/usr/bin/env python
 
LISTEN_PORT = 1431
SERVER_PORT = 143
 
from twisted.internet import protocol, reactor, defer
from email.parser import Parser
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
import email, imaplib, re, StringIO, ConfigParser, base64
from encryption import *

header_part = ['From', 'To', 'Subject']
Tokenize_append = "APPEND"
Tokenize_Login = "LOGIN"
Tokenize_authenticate = "authenticate plain"
Tokennize_capability = "capability"
config = ConfigParser.ConfigParser()
config.read("/home/minhvu/Desktop/ssee/config_proxy")

class ServerProtocol(protocol.Protocol):
	
	# Using self.client to connect Client-Proxy
	# Using self.other to get other function class
	# Using self.email_address to get the whole user's email_address 
	# Using self.flag to know which data we need

	def __init__(self):
		self.client = None
		#self.other = Other_Function()
		self.email_address = None
		self.buffer = None
		self.flag_Login = False
		self.flag_Append = False
		self.server = None
		self.d = defer.Deferred()

	# Create a connection between the first part and the second part of proxy
	def connectionMade(self):
		factory = protocol.ClientFactory()
		factory.protocol = ClientProtocol
		factory.server = self
		if self.server is None:
			self.transport.write(config.get('Fake_Command', 'connect_server') + '\r\n')
			print SERVER_ADDR
			self.d.addCallback(self.dataReceived)
			print SERVER_ADDR
		else:
			reactor.connectTCP(self.server, SERVER_PORT, factory)


	# The gate Client sending data to Proxy
	def dataReceived(self, data):
		print "C->S: %s", repr(data)

		if self.client:
			print "hehehehe"
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
			print "hohohoho"
			# login function
			if Tokenize_authenticate in data.upper():
				# Open the flag to get the new message
				self.flag_Login = True
			elif self.flag_Login == True:
				# Using base64 to decrypt information
				self.email_address = base64.b64decode(
					data.replace('\r\n','')).split('\x00')[1] + '@' + SERVER_ADDR
				self.flag_Login = False
			elif Tokenize_Login in data.upper() and len(data.split(' ')) == 4:
				# Some Email clients do not encrypted string, solving easily
				if "@" in data:
					self.server = config.get('Server', data.split(' ')[-2].split("@")[-1])
					self.d.addCallback(self.connectionMade)
				else:
					self.server = config.get('Server', 'ubuntu.com')
					self.d.addCallback(self.connectionMade)

			if Tokennize_capability in data.lower() and len(data.split(' ')) == 2:
				uid_command = data.split(' ')[0]
				curr_data_1 = config.get('Fake_Command', 'capability')
				curr_data_1 = curr_data_1.replace(curr_data_1.split('\\r\\n')[1].split(' ')[0]
					, uid_command)
				self.transport.write(curr_data_1.replace('\\r\\n', '\r\n') + '\r\n')
				self.buffer = None



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

def main():
	factory = protocol.ServerFactory()
	factory.protocol = ServerProtocol

	reactor.listenTCP(LISTEN_PORT, factory)
	reactor.run()
if __name__ == '__main__':
	main()