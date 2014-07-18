from summary_files import * 

# get data to decrypt
def dec_header_body(data_to_decrypt):
	print repr(data_to_decrypt)
	IV = binascii.unhexlify(data_to_decrypt.split(".")[1])
	data = binascii.unhexlify(data_to_decrypt.split(".")[0])
	return IV, data

# decrypt header value
def decrypt_RND_header_and_body_value(key, data_to_decrypt):
	IV, data = dec_header_body(data_to_decrypt)
	cipher = AES.new(key[:16], AES.MODE_CBC, IV[:16])
	data_to_be_decrypted = cipher.decrypt(data).replace(chr(0),"")
	return data_to_be_decrypted

# decrypt email
def decrypt_email(cipher_key, splat):
	store_dec_email = {}
	for i in splat:
		position_to_split = i.find(":")
		object_ = i[0:position_to_split].replace("\n","")
		if object_ != '':
			store_dec_email.update({object_:decrypt_RND_header_and_body_value(cipher_key,i)})
		else:
			continue
	store_Folder(get_email_count, store_dec_email, Folder_dec)
	return

# get email from encrypt folder
def get_email_dec(cipher_key, directory):
	for file in os.listdir(directory):
		if file.endswith('.txt'):
			print file
			f = open(os.path.join(directory, file), 'r')
			get_email_count = ''.join(x for x in file if x.isdigit())
			data = f.read()
			splat = data.split("\n\n\n")
			decrypt_email(cipher_key, splat, get_email_count)
	return