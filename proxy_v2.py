#!/usr/bin/env python
 
LISTEN_PORT = 1432
 
from twisted.internet import protocol, reactor, ssl
import email, imaplib, re, StringIO, ConfigParser, base64, sys, time
from encryption import *

header_part = ['From', 'To', 'Subject']

Tokenize_append = "APPEND"
Tokenize_Login = "LOGIN"
Tokenize_authenticate = 'authenticate plain'
Tokennize_capability = "capability"
Tokennize_A = "@"
Tokenize_Select = "select"
Tokenize_Inbox = ['inbox', 'inbox.']
Tokenize_Compress = 'COMPRESS'
Tokenize_Fetch = ['OK Fetch completed', 'OK Success']
Tokenize_Body = ['BODY[]', 'BODY[HEADER.', 'RFC822']

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
		self.flag_Fetch = False
		self.other = None
		self.folder_selection = ''

	# Create a connection between the first part and the second part of proxy

	def connectionMade(self):
		factory = protocol.ClientFactory()
		factory.protocol = ClientProtocol
		factory.server = self
		if self.factory.SERVER_ADDR == 'localhost':
			reactor.connectTCP(self.factory.SERVER_ADDR, self.factory.SERVER_PORT
				, factory)
		else:
			reactor.connectSSL(self.factory.SERVER_ADDR, self.factory.SERVER_PORT
				, factory, ssl.ClientContextFactory())

	# The gate Client sending data to Proxy
	def dataReceived(self, data):
		print "C->S: %s", repr(data)

		if self.client:

			# Login function to get data 
			if Tokenize_authenticate in data.lower():
				self.flag_Login = True
			elif self.flag_Login == True:
				self.other = Other_Functions(base64.b64decode(
					data.replace('\r\n','')).split('\x00')[1])
				self.flag_Login = False
			elif Tokenize_Login in data.upper() and len(data.split(' ')) == 4:
				if not Tokennize_A in data.split(' ')[-2]:
					self.other = Other_Functions(data.split(' ')[-2] + 
						'@ubuntu.com')
				else:
					self.other = Other_Functions(data.split(' ')[-2])

			# Appeding data to mail box
			if Tokenize_append in data.upper():
				message_length, curr_data = self.other._get_length(data)
				if message_length == len(curr_data) -2:
					self.client.write(self.other.Append(data))
					self.client.write('\r\n')
					return
				else:
					self.flag_Append = True
					self.buffer += data
					return
			elif self.flag_Append == True:
				self.buffer += data
				message_length, curr_data = self.other._get_length(self.buffer)
				if message_length == len(curr_data) -2:
					self.flag_Append = False
					self.client.write(self.other.Append(data))
					self.client.write('\r\n')
					return
				return

			if Tokenize_Select in data.lower():
				if len(data.split(' ')) > 3:
					self.folder_selection = data.split(' ')[-2].lower()
				else:
					self.folder_selection = data.split(' ')[-1].lower()
				if self.folder_selection.startswith('"') and self.folder_selection.endswith('"'):
					self.folder_selection = self.folder_selection[1:-1]

			self.client.write(data)
		else:						
			self.buffer = data

	# The gate Proxy sending data to Client
	def write(self, data):
		print "S->C: %s", repr(data)

		if len(filter(lambda x: x in self.folder_selection, Tokenize_Inbox)) > 0 and len(
			filter(lambda x: x in data, Tokenize_Fetch)) > 0 and len(filter(
			lambda x: x in data, Tokenize_Body)) > 0 and 'FETCH' in data.upper():
			self.transport.write(self.other.Transfer(data))
			return
		elif len(filter(lambda x: x in self.folder_selection, Tokenize_Inbox)) > 0 and len(
			filter(lambda x: x in data, Tokenize_Body)) > 0 and 'FETCH' in data.upper():
			self.flag_Fetch = True
			self.buffer += data
			return
		elif self.flag_Fetch == True:
			if len(filter(lambda x: x in data, Tokenize_Fetch)) > 0:
				self.flag_Fetch = False
				self.transport.write(self.other.Transfer(self.buffer + data))
				return
			else:
				self.buffer += data
				return

		if Tokenize_Compress in data:
			curr = data.split(Tokenize_Compress)[1]
			curr = ' '.join(curr.split(' ')[1:])
			data = data.split(Tokenize_Compress)[0] + curr

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
			, len(enc_email), 0)
		return append_cmd + enc_email

	def Changing_Length(self, data, new_length, flag):
		number = data.split("{")[-1].replace("}\r\n", "")
		if flag == 0:
			data = data.replace(str(number), str(new_length) + '+')
		else:
			data = data.replace(str(number), str(new_length))
		return data

	def _encrypted(self, data):
		enc_Preview = email.message_from_string('\r\n'.join(data.split(
			'\r\n')[1:]))
		plain_Preview = str(self.E.decrypt_email(enc_Preview)).replace(
			'\n', '\r\n')
		preview_cmd = self.Changing_Length(data.split('\r\n')[0] + '\r\n'
			, len(plain_Preview) + 2, 1)
		return preview_cmd + plain_Preview + '\r\n)\r\n'

	def Transfer(self, data):
		list_enc_Preview = data.split('\r\n)\r\n*')[:-1]
		if len(list_enc_Preview) > 0:
			return reduce(lambda x, y: x+y, map(self._encrypted
				, list_enc_Preview)) + data.split('\r\n)\r\n')[-1]
		else:
			enc_email = email.message_from_string('\r\n'.join(data.split('\r\n')[1:]))
			plain_email = str(self.E.decrypt_email(enc_email)).replace('\n', '\r\n')
			fetch_cmd = self.Changing_Length(data.split('\r\n')[0] + '\r\n'
				, len(plain_email), 1)
			fetch_tail = ')\r\n'  + data.split(')\r\n')[-1]
			return fetch_cmd + plain_email + fetch_tail

	def _get_length(self, data):
		number = int(data.split('\r\n')[0].split('{')[-1].replace('+}', ''))
		data = '\r\n'.join(data.split('\r\n')[1:])
		return number, data

def main(argv):
	factory = protocol.ServerFactory()
	if argv == 1:
		factory.SERVER_ADDR = 'imap.gmail.com'
		factory.SERVER_PORT = 993
		factory.protocol = ServerProtocol
		reactor.listenSSL(LISTEN_PORT, factory, ssl.DefaultOpenSSLContextFactory(
			'server.key', 'server.crt'))
	else:
		factory.SERVER_ADDR = 'localhost'
		factory.SERVER_PORT = 143
		factory.protocol = ServerProtocol
		reactor.listenTCP(LISTEN_PORT, factory)

	reactor.run()
if __name__ == '__main__':
	main(2)