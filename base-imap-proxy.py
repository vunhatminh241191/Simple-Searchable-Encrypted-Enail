#!/usr/bin/env python
 
LISTEN_PORT = 1431
SERVER_PORT = 143
SERVER_ADDR = "localhost"
 
from twisted.internet import protocol, reactor
from email.parser import Parser
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
import email, imaplib, re, StringIO
from summary_files import *

header_part = ['From', 'To', 'Subject']

class ServerProtocol(protocol.Protocol):
	def __init__(self):
		self.buffer = None
		self.client = None
		self.other = Other_Function()
		self.prf_key = None
		self.cipher_key = None
		self.user = None
		self.checking_append = False
		self.flag = False
 
	def connectionMade(self):
		factory = protocol.ClientFactory()
		factory.protocol = ClientProtocol
		factory.server = self
		self.prf_key, self.cipher_key = self.other.reading_key()
		reactor.connectTCP(SERVER_ADDR, SERVER_PORT, factory)

	# Client => Proxy
	def dataReceived(self, data):
		#print "C->S: %s", repr(data)

		if self.client:
			# Login, Append and Search commands
			if "LOGIN" in data:
				self.user = self.other.Login(data, self.prf_key)
			if "APPEND" in data:
				self.other.buffer += data
				self.checking_append = True
				self.transport.write('+ OK\r\n')
				return
			elif self.checking_append == True and self.flag == False:
				self.other.buffer += data
				self.flag = True
				return
			elif self.flag == True:
				if len(data) == 2:
					self.flag = False
					self.checking_append = False
					append_cmd, transfer_email =  self.other.Append(self.prf_key, 
						self.cipher_key, self.user)
					self.sending_append(append_cmd, transfer_email)
					return
				else:
					self.other.buffer += data
					return
			if "SEARCH" in data:
				data = self.other.Search(data, self.prf_key)

			self.client.write(data)
		else:
			self.buffer = data
 
	# Proxy => Client
	def write(self, data):
		#print "S->C: %s", repr(data)

		if "FETCH" and "OK Fetch completed" and "BODY[]" in data:
			self.other.Fetch(data)

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

class Other_Function(object):
	def __init__(self):
		self.buffer = ''
		self.f = open("testing.txt", 'w')

	def reading_key(self):
		with open('secret_key.txt') as f:
			first_key = f.readline().replace("\n","")
			second_key = f.readline().replace("\n", "")
			prf_key, cipher_key = PRF_and_Cipher_key(first_key, second_key)
		return prf_key, cipher_key

	def Login(self, data, prf_key):
		curr_data = data.split(' ')
		user = PRF(prf_key, curr_data[2], 10)
		return user

	def Append(self, prf_key, cipher_key, user):
		append_cmd = self.buffer.split('\r\n')[0] + "\r\n"
		email_ = email.message_from_string('\r\n'.join(self.buffer.split('\r\n')[1:]))
		encryption = Encryption(email_, cipher_key, prf_key, user)
		transfer_email = encryption.encrypted_email()
		append_cmd = self.change_length_http(append_cmd, len(transfer_email))
		self.buffer = ''
		return append_cmd, transfer_email

	def Search(self, data, prf_key):
		print data
		curr_data = data[data.index('"') + 1:data.rindex('"')]
		data_to_search = binascii.hexlify(PRF(prf_key, curr_data, 4))[:4]
		data = data.replace(curr_data, data_to_search)
		print data
		return data

	def Fetch(self, data):
		list_data = data.split("===--)")
		for member in list_data:
			print "hohohoho"
			print member
		

	def change_length_http(self, header_str, len_data):
		number = header_str.split("{")[-1].replace("}\r\n", "")
		header_str = header_str.replace(str(number), str(len_data))
		return header_str

	def get_message(self, data):
		header_str = data.split('\r\n')[0] + '\r\n'
		tail_str = ')\r\n' + data.split(')\r\n')[-1]
		message = data.split(header_str)[1].split(tail_str)[0]
		return header_str, tail_str, message

class Encryption(object):
	def __init__(self, data, cipher_key, prf_key, user):
		self.data = data
		self.cipher_key = cipher_key
		self.prf_key = prf_key
		self.user = user

	def encrypted_email(self):
		message = MIMEMultipart()
		enc_string = ''
		for header in header_part:
			if self.data[header]  == None or self.data[header] == '':       
				return
			message[header] = encrypt_header_body(self.cipher_key, 
				self.prf_key, self.data[header], 1)
			print message[header]
		for part in self.data.walk():
			if (part.get_content_maintype() == 'multipart') or (part.get_content_subtype() 
				!= 'plain'):
				continue
			body = part.get_payload()
			if body == None:
				return
			enc_body = encrypt_header_body(self.cipher_key, self.prf_key, body, 2)
			message.attach(MIMEText(enc_body))

		self.printout(message)

		return str(message)

	def printout(self, message):
		for header in header_part:
			print message[header]
		for part in message.walk():
			if (part.get_content_maintype() == 'multipart') or (part.get_content_subtype()
				!= 'plain'):
				continue
			print part.get_payload()

class Decryption(object):
	def __init__(self, data, cipher_key, user):
		self.data = data
		self.cipher_key = cipher_key
		self.user = user

	def decrypt_email(self):
		message = MIMEMultipart()
		dec_string = ''
		for header in header_part:
			if self.data[header]  == None or self.data[header] == '':           
				return
			message[header] = decrypt_RND_header_and_body_value(self.cipher_key,
				self.data[header])
		for part in self.data.walk():
			if (part.get_content_maintype() == 'multipart') or (part.get_content_subtype() 
				!= 'plain'):
				continue
			body = part.get_payload()
			if body == None:
				return
			dec_body = decrypt_RND_header_and_body_value(self.cipher_key, body)
			message.attach(MIMEText(dec_body))
		return str(message)
 
def main():
	factory = protocol.ServerFactory()
	factory.protocol = ServerProtocol
 
	reactor.listenTCP(LISTEN_PORT, factory)
	reactor.run()
 
if __name__ == '__main__':
	main()