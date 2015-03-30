import matplotlib.pyplot as plt
import os

path_name_graph = '/home/minh/Desktop/ssee/graph'

def create_directory(path_name):
	if not os.path.exists(path_name):
		os.makedirs(path_name)
	return os.path.abspath(path_name)


if __name__ == '__main__':
	list_word = {}
	graph_path = create_directory(path_name_graph)
	open_file = open('/home/minh/Desktop/ssee/10_day/AAA/finding_word.txt')
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
	plt.title("Graph Training")
	plt.plot(x, y)
	os.path.join(graph_path, plt.savefig("graph_10_day.png", dpi=100))
	plt.draw()
