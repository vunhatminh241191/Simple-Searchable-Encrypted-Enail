import glob, re, math, Crypto.Random, binascii, os
from decimal import *
from encryption import *
from collections import Counter
from scipy.stats import binom

def count_and_create_list(file_name, wordcount, testing_case):
	count = 0
	with open(file_name) as f:
		regex = re.compile('[^a-z]')
		for sentences in f.readlines():
			if len(sentences.split()) - 2 != testing_case:
				continue
			else:
				count += len(sentences.split()) -2

				words = sentences.lower().split()[2:]
				for word in words:
					testing_word = regex.sub('', word)
					if testing_word != '':
						word = testing_word
						if word not in wordcount:
							wordcount[word] = 1
						else:
							wordcount[word] += 1
		f.close()
	return count, wordcount

def probability_tag(dict_tag, guess_word, guess_word_percent_success, total_words):
	with open(guess_word + 'testing' + '.txt', 'w') as f:
		print_tag = {}
		for word, appearance in dict_tag.items():
			word_probability = binom.pmf(appearance, total_words, guess_word_percent_success)
			print_tag.update({word:word_probability})

		sort = sorted( ((v,k) for k,v in print_tag.iteritems()), reverse=True)

		for key, value in sort:
			f.write(str(key))
			f.write(':')
			f.write(str(value))
			f.write('\n')
		f.close

def percentage_plain_text(dictionary_word, total_words):
	word_percent = {}
	for word, appearance in dictionary_word.items():
		probability_success = float(appearance)/float(total_words)
		word_percent.update({word:probability_success})
	return word_percent

def get_list_file(link_file, list_file_name_comparing=[]):
	list_file_name = []
	for file_name in sorted(glob.glob(link_file)):
		if file_name in list_file_name_comparing:
			continue
		elif len(list_file_name) < 10:
			list_file_name.append(file_name)
		else:
			break
	return list_file_name

def writing_file(list_file_name=[], list_file_name_testing=[]):
	list_word_percent = []
	list_word_count = []

	if list_file_name == []:
		list_file_name_in_case = list_file_name_testing
		name_file = 'testing_file_next_10_case_'
	else:
		list_file_name_in_case = list_file_name
		name_file = 'training_file_first_10_case_'

	for i in xrange(1, 4):
		wordcount = {}
		total_words = 0
		with open(name_file + str(i) + '.txt' , 'w') as f:
			for file_name in list_file_name_in_case:
				counting_, wordcount = count_and_create_list(file_name, wordcount, i)
				total_words += counting_

			word_percent = percentage_plain_text(wordcount, total_words)
			
			list_word_percent.append(word_percent)
			list_word_count.append(wordcount)

			sort = sorted( ((v,k) for k,v in word_percent.iteritems()), reverse=True)
			for key, value in sort:
				f.write(str(key))
				f.write(':')
				f.write(str(value))
				f.write('\n')
			f.close()
		break
	return list_word_percent, list_word_count, total_words

def create_tag(list_wordcount_training):
	E = Encryption('chilun1403', 'chilun2411')
	salt = binascii.hexlify(Crypto.Random.get_random_bytes(16))
	list_number_word_tag = []

	for word_list in list_wordcount_training:
		list_word_tag = {}
		tag_word = {}
		for word, value in word_list.items():
			IV = E._create_IV('text', salt)
			word_tag = E.PRF(word)
			list_word_tag.update({word_tag:value})
			tag_word.update({word:word_tag})
		list_number_word_tag.append(list_word_tag)

		with open("testAAA.txt", 'w') as f:
			for key, value in tag_word.items():
				f.write(str(key))
				f.write(':')
				f.write(str(value))
				f.write('\n')
			f.close()
	return list_number_word_tag, tag_word

if __name__ == '__main__':
	
	list_file_name = get_list_file('/home/home/Downloads/Corpus/#ubuntu+1/*', [])
	list_file_name_testing = get_list_file('/home/home/Downloads/Corpus/#ubuntu+1/*', list_file_name)

	list_word_percent_training, list_wordcount_training, total_words = writing_file([], list_file_name_testing)

	list_number_word_tag, tag_word = create_tag(list_wordcount_training)

	

	for i in range(len(list_word_percent_training)):
		for word, value in list_word_percent_training[i].items():
			probability_tag(list_number_word_tag[i], word, value, total_words)


	#list_word_count_testing, list_wordcount_testing = writing_file([], list_file_name_testing)
		