import os
from encryption_1 import *

E = Encryption('chilun1403', 'chilun2411')
path_name = '/home/minh/Desktop/ssee/30_day/finding_word'
list_file_testing = ['/home/minh/Desktop/ssee/30_day/last_testing/1/1.txt', '/home/minh/Desktop/ssee/30_day/last_testing/2/2.txt', '/home/minh/Desktop/ssee/30_day/last_testing/3/3.txt']

def create_dir(path_name):
	if not os.path.exists(path_name):
		os.makedirs(path_name)
	return os.path.abspath(path_name)

if __name__ == '__main__':
	list_word = {}
	for i in xrange(3):
		list_file_word = open(list_file_testing[i])
		for line in list_file_word:
			word = line.split(':')[1].rstrip('\n')
			tag_word = E.PRF(word)
			word_training = open(os.path.dirname(list_file_testing[i]) + word + 'testing.txt')
			for i, line in enumerate(word_training):
				if tag_word in line:
					list_word.update({word:i})
					break
		list_word = sorted(((v,k) for k, v in list_word.iteritems()))

		with open(os.path.join(create_dir(path_name), 'finding_word_30_last_testing.txt'), 'wb') as f:
			for key, value in list_word:
				f.write(value)
				f.write(':')
				f.write(str(key))
				f.write('\n')
			f.close()