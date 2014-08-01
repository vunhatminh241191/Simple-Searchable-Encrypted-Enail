import binascii, string, re
from Crypto.Cipher import AES
from Crypto.Hash import HMAC
from Crypto.Hash import SHA256
from Crypto.Protocol.KDF import PBKDF2
import Crypto.Random
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText

stopwords = set("a an and be for from fw fwd if is it of on or re the than that this then".split())

class Encryption:

	# Tokenization methods:
	TOKENIZE_EMAIL_ADDRESSES = 0	# Used for header fields like From, To, CC
	TOKENIZE_BLANK_SPACES = 1		# Tokenize just on blank spaces (default)
	TOKENIZE_HEADER_PART = ['From', 'To', 'Cc', 'Bcc', 'Subject']
	# Number of characters for the tags
	__tag_length = 4

	# password: The user's password
	# salt: Salt for PBKDF2 or in our case, the user's email address
	def __init__(self, password, salt):
		prf = lambda password, salt: HMAC.new(password, salt, SHA256).digest()
		key = PBKDF2(password, salt, 48, 10000, prf)
		# First 128 bits are cipher key, Last 256 bits are tagging key
		self.__cipher_key = key[:16]
		self.__prf_key = key[16:]

	# Encrypts the given tag using an HMAC on SHA-256
	# tag: the tag to encrypt
	# Returns the SAH256 HMAC of the 'tag' using the given prf key in a string
	# of length 'self.__tag_length' encoded in hex
	def __PRF(self, tag):
		hmac = HMAC.new(key = self.__prf_key, msg = tag, digestmod = SHA256)
		return hmac.hexdigest()[:self.__tag_length]

	# Encrypt the given plaintext using the given key in AES CBC mode with
	# padding of the null character.
	# plaintext: plain text to encrypt
	# Return value is two hex strings for IV and cipher text
	def __encrypt(self, IV, plaintext):
		cipher = AES.new(self.__cipher_key, AES.MODE_GCM, IV)
		# Multiply the null character the needed number of times and append
		# This is needed because the AES function will not pad the string
		plaintext += chr(0) * (16-(len(plaintext) % 16))
		# Encrypt and return two pieces of binary data
		return binascii.hexlify(cipher.encrypt(plaintext)), binascii.hexlify(
			cipher.digest())

	# This function splits all the elements in the headers with lists of emails
	def __split_element(self, data):
		orig_toks = data.strip().lower().split()
		tokens = set([])
		# split again with the data input ori_toks
		for i in range(len(orig_toks)):
			tok = orig_toks[i]
			if (tok in stopwords) or (len(tok) < 2):
				continue
			if tok.startswith("<") and tok.endswith(">"):
				tok = tok[1:-1]
			if "@" in tok:
				newtoks = tok.split("@")
				tokens.update(newtoks)
			if "." in tok:
				newtoks = tok.split(".")
				tokens.update(newtoks)
			tokens.add(tok)
		return tokens

	# Just gets all the unique words from tokens
	def __get_unique_words(self, tokens):
		ulist = []
		[ulist.append(x) for x in tokens if x not in ulist]
		return ulist

	# Create full encryption string.
	# Returned Format is: mac.ciphertext.tag1.tag2...
	# plaintext: the plaintext of the field
	# tokenFlag: What kind of tokenization for the tags. (Use class constants)
	# snippetBlocks: If zero, do not make a preview, otherwise, tag and encrypt
	# this number of blocks at the beginning, used for body and subject.
	def encrypt_and_tag(self, IV, plaintext, tokenFlag, snippetBlocks):
		if tokenFlag == self.TOKENIZE_EMAIL_ADDRESSES:
			tokens = self.__get_unique_words(self.__split_element(plaintext))
		else:
			tokens = self.__get_unique_words(plaintext.split(' '))
		tags = []
		for token in tokens:
			tags.append(self.__PRF(token))
		# A block is 30 characters with space for padding
		if snippetBlocks > 0:
			snippet, s_digest = self.__encrypt(IV[16:]
				, plaintext[:snippetBlocks*15])
			ctext, c_digest = self.__encrypt(IV[:16], plaintext)
			digest = s_digest + '.' + snippet
			ciphertext = c_digest + '.' + ctext
		else:
			ciphertext, digest = self.__encrypt(IV[:16], plaintext)
		return digest + '.' + ciphertext + '.' + string.join(tags, '.') + '.'

	# Creates an ecnrypted tag from the given search term
	def create_tag(self, searchterm):
		return self.__PRF(searchterm)

	# Decrypts the given ciphertext. The tags can be attached at the end or
	# not, it won't affect the result.
	def decrypt(self, IV, ciphertext):
		sections = ciphertext.split('.')
		cipher = AES.new(self.__cipher_key, AES.MODE_GCM, IV)
		plaintext = cipher.decrypt(binascii.unhexlify(
			sections[1])).replace(chr(0), '')
		try:
			cipher.verify(binascii.unhexlify(sections[0]))
			return plaintext
		except ValueError:
			return "Message was corrupted"

	# Takes in a plain email and returns an encrypted one. Both the argument
	# and return value are dictionaries with the body stored under 'Body' and
	# other headers stored under their MIME names.
	def encrypt_email(self, plain_email):
		salt = binascii.hexlify(Crypto.Random.get_random_bytes(16))
		enc_email = MIMEMultipart()

		for header in self.TOKENIZE_HEADER_PART:
			IV = self._create_IV(header, salt)
			if header == 'Subject':
				enc_email[header] = self.encrypt_and_tag(IV, plain_email[header]
					, self.TOKENIZE_BLANK_SPACES, 1)
			else:
				if plain_email[header] != None:
					enc_email[header] = self.encrypt_and_tag(IV
						, plain_email[header]
						, self.TOKENIZE_EMAIL_ADDRESSES, 0)

		for part in plain_email.walk():
			IV = self._create_IV('Body', salt)
			if (part.get_content_maintype() == 'multipart') and (
				part.get_content_subtype() != 'plain'):
				continue
			body = part.get_payload()
			if body == None:
				return
			enc_body = self.encrypt_and_tag(IV, body
				, self.TOKENIZE_BLANK_SPACES, 2)
			enc_email.attach(MIMEText(enc_body))

		enc_email.replace_header('From', salt + '.' + enc_email['From'])
		
		return enc_email

	def _create_IV(self, header, salt):
		IV = SHA256.new(salt + header).digest()[:16]
		IV += SHA256.new(salt + header + 'Snippet').digest()[:16]
		return IV

	# Takes in a plain email and returns an encrypted one. Both the argument
	# and return value are dictionaries with the body stored under 'Body' and
	# other headers stored under their MIME names.
	def decrypt_email(self, enc_email):
		salt = enc_email['From'][:32]
		enc_email['From'] = enc_email['From'][33:]
		plain_email = MIMEMultipart()

		for header in self.TOKENIZE_HEADER_PART:
			IV = SHA256.new(salt+ header).digest()[:16]
			if header == 'Subject':
				plain_email[header] = self.decrypt(IV, enc_email[header][
					66:enc_email[header].find('.', 99)+1])
		for key in enc_email:
			key = key.lower().capitalize()
			IV = SHA256.new(salt + key).digest()[:16]
			if key == 'Body':
				plain_email[key] = self.decrypt(IV, enc_email[key][
					98:enc_email[key].find('.', 131)+1])
			elif key == 'Subject':
				plain_email[key] = self.decrypt(IV, enc_email[key][
					66:enc_email[key].find('.', 99)+1])
			elif key in ['From', 'To', 'Cc', 'Bcc']:
				plain_email[key] = self.decrypt(IV, enc_email[key])
		return plain_email
