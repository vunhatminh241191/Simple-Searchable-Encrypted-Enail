import sys
from encryption_1 import *

E = Encryption('chilun1403', 'chilun2411')
path_name_finding_word = open('/home/minh/Desktop/ssee/10_day/AAA/finding_word_testing.txt','w')


if __name__ == '__main__':
	list_word = {}
	list_file_word = open('/home/minh/Desktop/ssee/10_day/next_testing/1/1.txt')
	for line in list_file_word:
		word = line.split(':')[1].rstrip('\n')
		tag_word = E.PRF(word)
		word_training = open('/home/minh/Desktop/ssee/10_day/next_testing/1/' + word + 'testing.txt')
		for i, line in enumerate(word_training):
			if tag_word in line:
				list_word.update({word:i})
				break
	list_word = sorted(((v,k) for k, v in list_word.iteritems()))

	for key, value in list_word:
		path_name_finding_word.write(value)
		path_name_finding_word.write(':')
		path_name_finding_word.write(str(key))
		path_name_finding_word.write('\n')
	path_name_finding_word.close()