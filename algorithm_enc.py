from summary_files import *

stopwords = set("a an and be for from fw fwd if is it of on or re the than that this then".split())

# PRF function with key, message and prf len
def PRF(key, message, prflen):
	hash_input = message
	while len(hash_input) % 16 != 0:
		hash_input += ''.join(chr(ord(a) ^ ord(b)) for a,b in zip (hash_input, chr(0)))
	hmac = HMAC.new(key = key, msg = hash_input, digestmod = SHA)
	prf = hmac.digest()
	# if decrypt_prf, we will have the hmac.digest()
	return prf

# def PRF and Cipher_key
def PRF_and_Cipher_key(prf_plaintext, cipher_plaintext):
	prf_key = SHA.new(prf_plaintext).digest()
	cipher_key = SHA.new(cipher_plaintext).digest()
	return prf_key, cipher_key

# encrypt_RND function with key and plaintext
def encrypt_RND(key, plaintext):
	IV = SHA.new(plaintext).digest()
	cipher = AES.new(key[:16], AES.MODE_CBC, IV[:16])
	while len(plaintext) % 16 != 0:
		plaintext += chr(0)
	return IV, cipher.encrypt(plaintext)

# encrypt header email
def encrypt_header_body(cipher_key, prf_key, data, flag):
	if flag == 1:
		tokens = unique_word(split_element(data))
	else:
		tokens = unique_word(data.split(" "))
	tags = PRF_tokens(prf_key, tokens, 4)
	return combine_string_encrypted(tags, cipher_key, data)

def PRF_tokens(prf_key, tokens, prf_len):
	tags = []
	for tok in tokens:
		tag = PRF(prf_key, tok, prf_len)
		tags.append(tag)
	return tags

def combine_string_encrypted(tags, cipher_key, data):
	IV, ciphertext = encrypt_RND(cipher_key, data)
	dec_result = binascii.hexlify(ciphertext) + "." + binascii.hexlify(IV) + "."
	for tag in tags:
		dec_result += binascii.hexlify(tag)[:5] + "."
	return dec_result

# split each element in email header
def split_element(data):
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

def unique_word(tokens):
	ulist = []
	[ulist.append(x) for x in tokens if x not in ulist]
	return ulist