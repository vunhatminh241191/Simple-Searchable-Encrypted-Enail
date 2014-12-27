import glob, re, math, Crypto.Random, binascii, os
from decimal import *
from encryption_1 import *
from collections import Counter
from scipy.stats import binom

directory = '/home/minh/Downloads/Corpus/#ubuntu+1/*'
path_name_testing = '/home/minh/Desktop/ssee/10_day/next_testing_probability_training'
path_name_training = '/home/minh/Desktop/ssee/10_day/training'
path_name_AAA = '/home/minh/Desktop/ssee/60_day/AAA'

def get_list_file_name(link_file, list_file_comparing=[]):
	list_file_ = []
	for file_name in link_file:
		if file_name in list_file_comparing:
			continue
		elif len(list_file_) < 10:
			list_file_.append(file_name)
		else:
			return list_file_

def creating_dir(path_name):
	if 'AAA' in path_name:
		if not os.path.exists(path_name):
			os.makedirs(path_name)
		return os.path.abspath(path_name)
	else:
		list_directory = []
		for i in xrange(1,4):
			curr_path_name = os.path.join(path_name, str(i))
			if not os.path.exists(curr_path_name):
				os.makedirs(curr_path_name)
			list_directory.append(os.path.abspath(curr_path_name))
		return list_directory


def prepare_writing_file(list_file_training, list_file_testing
	, directory_training, directory_testing):

	list_word_percentage_training, list_word_count_training, total_words_training = writing_file(
		list_file_training, directory_training)

	list_word_percentage_testing, list_word_count_testing, total_words_testing = writing_file(
		list_file_testing, directory_testing)

	return list_word_count_training, list_word_percentage_training, list_word_count_testing, list_word_percentage_testing, total_words_training, total_words_testing

def writing_file(list_file_, directory):
	list_word_percentage = []
	list_word_count = []

	for i in xrange(1,4):
		word_count = {}
		total_words = 0
		case_directory = directory[i-1]
		file_name = str(i) + '.txt'
		with open(os.path.join(case_directory, file_name), 'wb') as f:
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
		for sentences in f.readlines():
			if len(sentences.split()) - 2 != testing_case:
				continue
			else:
				count += 1
				cur_words = ''
				words = ' '.join(sentences.lower().split()[2:])
				if len(words.split()) == 1:
					cur_words = regex_words(words)
				else:
					for word in words.split():
						cur_words += regex_words(word) + ' '
				if len(words.split()) != len(cur_words.split()) or cur_words == '':
					continue
				else:
					words = cur_words
				if words not in word_count:
					word_count[words] = 1
				else:
					word_count[words] += 1
		f.close()
	return count, word_count

def regex_words(word):
	regex = re.compile('[^a-z]')
	testing_word = regex.sub('', word)
	if testing_word != '':
		return testing_word
	return ''

def percentage_plain_text(word_count, total_words):
	word_percent = {}
	for word, appearance in word_count.items():
		probability_success = float(appearance)/float(total_words)
		word_percent.update({word:probability_success})
	return word_percent

def create_tag(list_wordcount_training, name, directory_AAA):
	E = Encryption('chilun1403', 'chilun2411')
	salt = binascii.hexlify(Crypto.Random.get_random_bytes(16))
	list_number_word_tag = []

	for i in range(len(list_wordcount_training)):
		list_word_tag = {}
		tag_word = {}
		for word, value in list_wordcount_training[i].items():
			IV = E._create_IV('text', salt)
			word_tag = E.PRF(word)
			list_word_tag.update({word_tag:value})
			tag_word.update({word:word_tag})
		list_number_word_tag.append(list_word_tag)

		file_name = str(i+1) + name + '.txt'

		with open(os.path.join(directory_AAA, file_name), 'wb') as f:
			for key, value in tag_word.items():
				f.write(str(key))
				f.write(':')
				f.write(str(value))
				f.write('\n')
			f.close()
	return list_number_word_tag

def probability_tag(dict_tag, guess_word, guess_word_percent_success, total_words
	, directory, name):
	file_name = guess_word + name + '.txt'
	with open(os.path.join(directory, file_name), 'wb') as f:
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

	list_file_training = get_list_file_name(sorted(glob.glob(directory)), [])
	list_file_testing = get_list_file_name(sorted(glob.glob(directory)), list_file_training)

	directory_training = creating_dir(path_name_training)
	directory_testing = creating_dir(path_name_testing)
	directory_AAA = creating_dir(path_name_AAA)

	list_word_count_training, list_word_percentage_training, list_word_count_testing, list_word_percentage_testing, total_words_training, total_words_testing = prepare_writing_file(
		list_file_training, list_file_testing, directory_training, directory_testing)

	#list_number_word_tag_training = create_tag(list_word_count_training, 'training', directory_AAA)

	list_number_word_tag_testing = create_tag(list_word_count_testing, 'next_testing_probability_training', directory_AAA)

	'''for i in range(len(list_word_percentage_training)):
		for word, value in list_word_percentage_training[i].items():
			probability_tag(list_number_word_tag_training[i], word, value, total_words_training
				, directory_training[i], 'training')'''

	'''for i in range(len(list_word_percentage_testing)):
		for word, value in list_word_percentage_testing[i].items():
			probability_tag(list_number_word_tag_testing[i], word, value, total_words_testing
				, directory_testing[i], 'testing')'''

	for i in xrange(len(list_word_percentage_testing)):
		for word, value in list_word_percentage_testing[i].items():
			if word in list_word_percentage_training[i]:
				probability_tag(list_number_word_tag_testing[i], word, list_word_percentage_training[i][word],
					total_words_testing, directory_testing[i], 'testing')
			else:
				probability_tag(list_number_word_tag_testing[i], word, 0, total_words_testing,
					directory_testing[i], 'testing')