from bs4 import BeautifulSoup
from urllib.request import urlopen
from urllib.request import HTTPError
import json

def get_2014_round_one():
	matches = []
	for i in range(1, 5):
		url = 'http://www.wimbledon.com/en_GB/scores/draws/ms/r1s' + str(i) + '.html'
		players_soup = get_soup(url)
		prev_name = None
		for item in players_soup.find_all('a', {'class' : 'sc'}):
			name = item.text
			if len(name) > 1:
				if prev_name == None:
					prev_name = name
				else:
					match = {}
					match['player_1'] = prev_name
					match['player_2'] = name
					match['score'] = ''
					match['winner'] = ''
					matches.append(match)
					prev_name = None
	list_matches(matches)

def get_draw(year):
	draw = {}
	url = 'http://www.atpworldtour.com/Share/Event-Draws.aspx?e=540&y=' + str(year)
	draw_soup = get_soup(url)
	for i in range(1, 9):
		draw[i] = get_round_listing(draw_soup, i)
	return update_draw_with_winners(draw)

def update_draw_with_winners(draw):
	for i in range(1, len(draw)):
		curr_round = draw[i]
		next_round = draw[i + 1]
		for x in range(0, len(curr_round)):
			winner = get_winner(x, curr_round, next_round)
			curr_match = curr_round[x]
			curr_match['winner'] = winner[0]
			curr_match['score'] = winner[1]
			try:
				curr_match.pop('player_1_score')
				curr_match.pop('player_2_score')
			except KeyError as e:
				continue
	return draw



def get_round_listing(draw_soup, round):
	matches = []
	i = 0
	prev_name = None
	prev_score = None
	while i <= (128 / (2**(round - 1))) - 1:
		id_base = ''
		if i < 10:
			id_base = 'cphMain_phExtra_ctl00_ctl0' + str(round) + '_ctl0' + str(i)
		else:
			id_base = 'cphMain_phExtra_ctl00_ctl0' + str(round) + '_ctl' + str(i)

		name_id = id_base + '_Player1Link'
		score_id = id_base + '_ScoreLink'

		raw_name = draw_soup.find('a', {'id' : name_id}).text
		player_name = get_formatted_name(raw_name)

		match = {}
		match['round'] = round
		player_score = ''
		if round > 1:
			player_score = draw_soup.find('a', {'id' : score_id}).text
		if i % 2 != 0 and round < 8:
			if round > 1 and len(player_score) > 0:
				match['player_1_score'] = prev_score
				match['player_2_score'] = player_score
			match['player_1'] = prev_name
			match['player_2'] = player_name
			matches.append(match)
		elif round == 8:
			match['player_1_score'] = player_score
			match['player_2_score'] = player_score
			match['player_1'] = player_name
			match['champion'] = player_name
			matches.append(match)

		prev_score = player_score
		prev_name = player_name

		i += 1
	return matches

last_next_match_number = -1

def get_winner(match_number, round, next_round):
	global last_next_match_number
	match = round[match_number]
	player1 = match['player_1']
	player2 = match['player_2']

	next_match_number = ((match_number + 2) // 2) - 1
	next_round_match = next_round[next_match_number]

	return_player = ''
	if player1 in next_round_match.values():
		return_player = player1
	elif player2 in next_round_match.values():
		return_player = player2

	return_score = ''
	if last_next_match_number != next_match_number and 'player_1_score' in next_round_match.keys():
		return_score = next_round_match['player_1_score']
	elif last_next_match_number == next_match_number and 'player_2_score' in next_round_match.keys():
		return_score = next_round_match['player_2_score']

	last_next_match_number = next_match_number
	return (return_player, return_score)

def get_champion(year):
	url = 'http://www.atpworldtour.com/Share/Event-Draws.aspx?e=540&y=' + str(year)
	winner_soup = get_soup(url)
	id = "cphMain_phExtra_ctl00_ctl08_ctl00_Player1Link"
	raw_name = winner_soup.find('a', {'id' : id}).text
	return get_formatted_name(raw_name)

def list_matches(matches):
	print('----------DRAW (ROUND OF ' + str(len(matches)) + ")----------")
	for match in matches:
		print(match['player_1'] + " VS " + match['player_2'] + " | WINNER: " + match['winner'] + " | SCORE: " + match['score'])

def get_formatted_name(name):
	comma_index = name.index(',')
	last_name = name[0:comma_index]
	first_name = name[comma_index + 2:]
	return first_name + " " + last_name


def get_soup(url):
	page = urlopen(url)
	source = page.read()
	page.close()
	return BeautifulSoup(source)