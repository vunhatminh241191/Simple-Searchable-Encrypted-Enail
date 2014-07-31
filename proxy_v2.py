#!/usr/bin/env python
 
LISTEN_PORT = 1431
SERVER_PORT = 143
 
from twisted.internet import protocol, reactor, defer
from email.parser import Parser
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
import email, imaplib, re, StringIO, ConfigParser, base64, sys
from encryption import *

header_part = ['From', 'To', 'Subject']

Tokenize_append = "APPEND"
Tokenize_Login = "LOGIN"
Tokenize_authenticate = "authenticate plain"
Tokennize_capability = "capability"
Tokennize_A = "@"
Tokenize_Select = "select"
Tokenize_Inbox = '"INBOX"'

config = ConfigParser.ConfigParser()
config.read("/home/minhvu/Desktop/ssee/config_proxy")


class ServerProtocol(protocol.Protocol):
	
	# Using self.client to connect Client-Proxy
	# Using self.other to get other function class
	# Using self.email_address to get the whole user's email_address 
	# Using self.flag to know which data we need

	def __init__(self):
		self.client = None
		self.buffer = None
		self.flag_Login = False
		self.flag_Append = False
		self.d = defer.Deferred()
		self.other = None
		self.folder_selection = None

	# Create a connection between the first part and the second part of proxy

	def connectionMade(self):
		factory = protocol.ClientFactory()
		factory.protocol = ClientProtocol
		factory.server = self
		reactor.connectTCP(self.factory.SERVER_ADDR, SERVER_PORT, factory)

	# The gate Client sending data to Proxy
	def dataReceived(self, data):
		print "C->S: %s", repr(data)

		if self.client:

			# Login function to get data 
			user_address = '' 
			if Tokenize_authenticate in data.upper():
				# Open the flag to get the new message
				self.flag_Login = True
			elif self.flag_Login == True:
				# Using base64 to decrypt information, bc IMAP extension using 
				# base64 to encode data "Authenticate Command"
				user_address = base64.b64decode(
					data.replace('\r\n','')).split('\x00')[1]
			elif Tokenize_Login in data.upper() and len(data.split(' ')) == 4:
				user_address = data.split(' ')[-2]
			if not Tokennize_A in data:
				#check if user_address is right or wrong
				user_address = user_address + '@ubuntu.com'
			#create prf_key and cipher_key
			self.other = Other_Functions(user_address)
			self.flag_Login = False

			# Appeding data to mail box
			if Tokenize_append in data.upper():
				self.flag_Append = True
				self.buffer += data
				return
			# Waiting more data until see "\r\n"
			elif self.flag_Append == True:
				if len(data) == 2:
					self.flag_Append = False
					self.client.write(self.other.Append(self.buffer))
					self.client.write('\r\n')
					return
				else:
					self.buffer += data
					return

			if Tokenize_Select in data.lower():
				self.folder_selection = data.split(' ')[-2]

			self.client.write(data)
		else:						
			self.buffer = data

	# The gate Proxy sending data to Client
	def write(self, data):
		print "S->C: %s", repr(data)

		print self.folder_selection

		if (self.folder_selection == Tokenize_Inbox) and (
			"FETCH" and "OK Fetch completed" and "BODY[]" in data):
			data = self.other.Fetch(data)

		'''elif (self.folder_selection == Tokenize_Inbox) and (
			"FETCH" and "RFC822.SIZE" in data):
			#data = self.other.Preview(data, self.cipher_key)
			return'''

		self.transport.write(data)


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

class Other_Functions(object):
	def __init__(self, email_address):
		self.E = Encryption(config.get('Proxy', 'pass_proxy'), email_address)

	def Append(self, data):
		plain_email = email.message_from_string('\r\n'.join(data.split('\r\n')[1:]))
		enc_email = str(self.E.encrypt_email(plain_email)).replace('\n', '\r\n')
		append_cmd = self.Changing_Length(data.split('\r\n')[0] + '\r\n'
			, len(enc_email))
		return append_cmd + enc_email

	def Changing_Length(self, data, new_length):
		number = data.split("{")[-1].replace("}\r\n", "")
		data = data.replace(str(number), str(new_length) + '+')
		return data

	def Fetch(self, data):
		enc_email = email.message_from_string('\r\n'.join(data.split('\r\n')[1:]))
		plain_email = str(self.E.decrypt_email(enc_email).replace('\n', '\r\n'))
		print repr(plain_email)


def main(argv):
	factory = protocol.ServerFactory()
	if len(argv) == 1:
		factory.SERVER_ADDR = config.get('Server', argv[0])
	else:
		factory.SERVER_ADDR = 'localhost'
	factory.protocol = ServerProtocol


	reactor.listenTCP(LISTEN_PORT, factory)
	reactor.run()
if __name__ == '__main__':
	main(sys.argv[1:])