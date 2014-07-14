import imaplib, getpass, email
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText

def login(username, password):
	rc, response = M.login(username,password)

# logout gmail account after finishing
def logout():
	M.logout

# get email function
def get_email(get_email_at_position):
	M.select("arnold-j.bridge")
	reps, data = M.FETCH(get_email_at_position,'(RFC822)')
	mail = email.message_from_string(data[0][1])
	return mail

if __name__ == '__main__':
	IMAP_SERVER = 'localhost'
	IMAP_PORT = 1432
	M = imaplib.IMAP4(IMAP_SERVER, IMAP_PORT)
	header_part = ['From', 'To', 'Subject']
	user = 'arnold-j'
	password = 'pass'
	login(user, password)
	'''get_email_count = 1
	for i in range(get_email_count):
		check_empty = False
		mail = get_email(i+1)
		message = MIMEMultipart()
		for header in header_part:
			if len(mail[header]) > 998:
				print i
			message[header] = mail[header]
		for part in mail.walk():
			if part.get_content_maintype() == 'multipart' or part.get_content_subtype() != 'plain':
				continue
			message.attach(MIMEText(part.get_payload()))
		M.append("Inbox", 'Inbox', None, str(message))'''
	M.select("Inbox")
	for i in ['From', 'To', 'Subject', 'Body']:
		status, data_list = M.search(None, i, '"jennifer.medcalf"')
		print data_list
		if data_list == ['']:
			continue
		else:
			for num in data_list[0].split():
				print num
				reps, data = M.FETCH(num, '(RFC822)')
				mail = email.message_from_string(data[0][1])
				for header in header_part:
					print repr(mail[header])
				for part in mail.walk():
					if part.get_content_maintype() == 'multipart' or part.get_content_subtype() != 'plain':
						continue
					print repr(part.get_payload())