from bs4 import BeautifulSoup
from urllib.request import urlopen
from urllib.request import HTTPError
import json

def get_draw_player_names():
	matches = []
	for i in range(1, 5):
		url = 'http://www.wimbledon.com/en_GB/scores/draws/ms/r1s' + str(i) + '.html'
		players_soup = getSoup(url)
		prevname = None
		for item in players_soup.find_all('a', {'class' : 'sc'}):
			name = item.text
			if len(name) > 1:
				if prevname == None:
					prevname = name
				else:
					matches.append((prevname, name))
					prevname = None
	for player1, player2 in matches:
		print(str(player1) + " VS " + str(player2))


def getSoup(link):
	page = urlopen(link)
	source = page.read()
	page.close()
	return BeautifulSoup(source)