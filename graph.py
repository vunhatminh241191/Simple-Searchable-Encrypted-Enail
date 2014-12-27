import matplotlib.pyplot as plt
import numpy as np

if __name__ == '__main__':
	list_word = {}
	open_file = open('/home/minh/Desktop/ssee/10_day/AAA/finding_word_testing.txt')
	for line in open_file:
		word, number = line.rstrip('\n').split(':')[0], int(line.rstrip('\n').split(':')[1])
		list_word.update({word:number})
	list_word = sorted(((v,k) for k, v in list_word.iteritems()))
	
	x = []
	y = []
	my_stick = []
	for i in xrange(len(list_word)):
		x.append(i)
		y.append(list_word[i][0])
		my_stick.append(list_word[i][1])

	plt.xticks(x, my_stick)
	plt.plot(x, y)
	plt.show()
