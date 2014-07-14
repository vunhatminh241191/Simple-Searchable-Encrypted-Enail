import imaplib, os, email
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
 
IMAPSERVER = 'imap.mail.yahoo.com'
IMAPPORT = '993'
directory = '/home/minhvu/test_user/arnold-j/Maildir/cur'
 
if __name__ == '__main__':
    M = imaplib.IMAP4_SSL(IMAPSERVER, IMAPPORT)
    user = 'emailresearchpdx@yahoo.com'
    password = 'MinhFletcher123'
    rc, response = M.login(user, password)
    for filename in os.listdir(directory):
        with open(os.path.join(directory, filename), "r") as f:
            msg = email.message_from_file(f)
            f.close()
            M.append("Encryption2", None, None, msg.as_string())

