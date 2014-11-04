import glob, re, math, Crypto.Random, binascii, os
from decimal import *
from encryption_1 import *
from collections import Counter
from scipy.stats import binom

directory = '/home/minh/Downloads/Corpus/#ubuntu+1/*'
path_name_testing = '/home/minh/Desktop/Research/10_day/testing'
path_name_training = '/home/minh/Desktop/Research/10_day/training'

def get_list_file_name(link_file, list_file_comparing=[]):
	list_file_ = []
	for file_name in sorted(glob.glob(link_file)):
		if file_name in list_file_comparing:
			continue
		elif len(list_file_) < 10:
			list_file_.append(file_name)
		else:
			return list_file_

def creating_dir(path_name):
	if not os.path.exists(path_name):
		os.makedirs(path_name)
	return os.path.abspath(path_name)


def prepare_writing_file(list_file_training, list_file_testing
	, directory_training, directory_testing):

	name_file_training = os.path.join(directory_training, 'training_first_10_days_case_')
	name_file_testing = os.path.join(directory_testing, 'testing_next_10_day_case_')

	list_word_percentage_training, list_word_count_training, total_words_training = writing_file(
		list_file_training, name_file_training)

	list_word_percentage_testing, list_word_count_testing, total_words_testing = writing_file(
		list_file_testing, name_file_testing)

	return list_word_count_training, list_word_percentage_training, list_word_count_testing, list_word_percentage_testing, total_words_training, total_words_testing
def writing_file(list_file_, directory):
	list_word_percentage = []
	list_word_count = []

	for i in xrange(1,4):
		word_count = {}
		total_words = 0
		with open(directory + str(i) + '.txt', 'wb') as f:
			for file_name in list_file_:
				counting, word_count = count_and_create_list(file_name, word_count, i)
				total_words += counting

			word_percentage = percentage_plain_text(word_count, total_words)
			list_word_percentage.append(word_percentage)
			list_word_count.append(word_count)

			sort = sorted( ((v,k) for k,v in word_percentage.iteritems()), reverse=True)
			for key, value in sort:
				f.write(str(key))
				f.write(':')
				f.write(str(value))
				f.write('\n')
			f.close()
	return list_word_percentage, list_word_count, total_words

def count_and_create_list(file_name, word_count, testing_case):
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
						if word not in word_count:
							word_count[word] = 1
						else:
							word_count[word] += 1
		f.close()
	return count, word_count

def percentage_plain_text(word_count, total_words):
	word_percent = {}
	for word, appearance in word_count.items():
		probability_success = float(appearance)/float(total_words)
		word_percent.update({word:probability_success})
	return word_percent

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
	return list_number_word_tag

def probability_tag(dict_tag, guess_word, guess_word_percent_success, total_words
	, directory):
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

if __name__ == '__main__':

	list_file_training = get_list_file_name(directory, [])
	list_file_testing = get_list_file_name(directory, list_file_training)

	directory_training = creating_dir(path_name_training)
	directory_testing = creating_dir(path_name_testing)

	list_word_count_training, list_word_percentage_training, list_word_count_testing, list_word_percentage_testing, total_words_training, total_words_testing = prepare_writing_file(
		list_file_training, list_file_testing, directory_training, directory_testing)

	list_number_word_tag_training = create_tag(list_word_count_training)

	list_number_word_tag_testing = create_tag(list_word_count_testing)

	for i in range(len(list_word_percentage_training)):
		for word, value in list_word_percentage_training[i].items():
			probability_tag(list_number_word_tag_training[i], word, value, total_words_training
				, directory_training)

	for i in range(len(list_word_percentage_testing)):
		for word, value in list_word_percentage_testing[i].items():
			probability_tag(list_number_word_tag_testing[i], word, value, total_words_testing
				, directory_testing)