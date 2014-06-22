from bs4 import BeautifulSoup
from urllib.request import urlopen
from urllib.request import HTTPError
import urllib
import json
from datetime import datetime

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

def get_draws(start_year, end_year):
	for i in range(start_year, end_year + 1):
		print('Getting draw for ' + str(i))
		write_draw(i, get_draw(i))

def get_draws_last_ten_years():
	get_draws(2003, 2013)

def write_draw(year, draw):
	info_file = open('wimbledon_draw_' + str(year) + '.txt', 'w')
	info_file.write(json.dumps(draw, indent=4, sort_keys=True))
	info_file.close()

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


def load_json(filename):
	opened_file = open(filename)
	raw = opened_file.read()
	opened_file.close()
	return json.loads(raw)

def get_soup(url):
	page = urlopen(url)
	source = page.read()
	page.close()
	return BeautifulSoup(source)

def load_draw(year):
	filename = 'wimbledon_draw_' + str(year) + '.txt'
	return load_json(filename)

def get_h2h_prediction_accuracy(start_year, end_year):
	h2h_total = 0
	h2h_accurate = 0
	for year in range(start_year, end_year + 1):
		draw = load_draw(year)
		for i in range(1, 8):
			round = draw[str(i)]
			for match in round:
				player_one = match['player_1']
				player_one_h2h = match['player_1_h2h']
				player_two = match['player_2']
				player_two_h2h = match['player_2_h2h']
				winner = match['winner']
				if player_one_h2h != player_two_h2h and (player_one_h2h > 0 or player_two_h2h) > 0:
					h2h_total += 1
					if player_one_h2h > player_two_h2h and winner == player_one or player_two_h2h > player_one_h2h and winner == player_two:
						h2h_accurate += 1
	return('Total head-to-heads: ' + str(h2h_total) + '\nAccurate head-to-heads: ' + str(h2h_accurate) + '\nPercentage' + str((h2h_accurate / h2h_total)))

def load_tournaments_file():
	return load_json('tournaments.txt')


def get_tournament_date(tournaments, name, url):
	if name not in tournaments:
		if len(url) > 1:
			tournament_url = 'http://www.atpworldtour.com' + url
			tournament_soup = get_soup(tournament_url)
			date = ''
			for item in tournament_soup.find_all('li'):
				strong = item.find('strong')
				if  strong != None and strong.text == "Date:":
					date = item.text[6:]
			tournaments[name] = date[:date.index('-')]
			tournaments_file = open('tournaments.txt', 'w')
			tournaments_file.write(json.dumps(tournaments, indent=4, sort_keys=True))
			tournaments_file.close()
			return date[:date.index('-')]
		else:
			return '31.12.2014'
	else:
		return tournaments[name]



def update_draws_with_h2h(start_year, end_year):
	for year in range(start_year, end_year + 1):
		ids_dict = json.loads(load_atp_ids_file())
		draw = load_draw(year)
		for i in range(1, 8):
			curr_round = draw[str(i)]
			for match in curr_round:
				h2h = get_head_to_head(ids_dict, year, match['player_1'], match['player_2'])
				match['player_1_h2h'] = h2h[0]
				match['player_2_h2h'] = h2h[1]
		write_draw(year, draw)


def get_head_to_head(ids_dict, year, player_one, player_two):
	tournaments_dict = load_tournaments_file()
	date_format = '%d.%m.%Y'
	wimbledon_date = datetime.strptime('23.06.2014', date_format)
	url = 'http://www.atpworldtour.com/Players/Head-To-Head.aspx?pId=' + ids_dict[player_one] + '&oId=' + ids_dict[player_two]
	print('Accessing ' + url)
	h2h_soup = get_soup(url)
	strongs = h2h_soup.find_all('strong')
	tournaments = []
	for link in h2h_soup.find_all('a'):
		if ('/Tennis/Tournaments/' in link['href'] or link['href'] == '#') and link.find('strong') != None:
			tournaments.append((link.text, link['href']))
	i = 0
	x = 0
	player_one_count = 0
	player_two_count = 0
	while i < len(strongs) and x < len(tournaments):
		tournament = tournaments[x]
		tournament_name = tournament[0]
		tournament_url = tournament[1]
		date_string = get_tournament_date(tournaments_dict, tournament_name, tournament_url)
		date = datetime.strptime(date_string, date_format)
		match_year = int(strongs[i].text)
		if match_year < year or match_year == year and date < wimbledon_date:
			winner = strongs[i+2].text
			formatted_winner = get_formatted_name(winner)
			if formatted_winner == player_one:
				player_one_count += 1
			elif formatted_winner == player_two:
				player_two_count += 1
		x += 1
		i += 3
	return (player_one_count, player_two_count)

def get_atp_ids_for_years(start_year, end_year):
	for i in range(start_year, end_year + 1):
		get_atp_ids(get_draw(i))

def load_atp_ids_file():
	players_file = open('players_atp.txt')
	players = players_file.read()
	players_file.close()
	return players

def get_atp_ids(draw):
	base_url = 'http://www.atpworldtour.com/Handlers/AutoComplete.aspx?q='
	players = load_atp_ids_file()
	atp_ids = {}
	try:
		atp_ids = json.loads(players)
	except Exception as e:
		print(e)
		atp_ids = {}
	round_one = draw[1]
	for match in round_one:
		player_1 = match['player_1']
		player_2 = match['player_2']
		if player_1 not in atp_ids:
			request_url = base_url + urllib.parse.quote_plus(player_1)
			print('Accessing ' + request_url)
			id_data = make_json_request(request_url)
			atp_ids[player_1] = id_data[0]['pid']
		if player_2 not in atp_ids:
			request_url = base_url + urllib.parse.quote_plus(player_2)
			print('Accessing ' + request_url)
			id_data = make_json_request(request_url)
			atp_ids[player_2] = id_data[0]['pid']

	players_file = open('players_atp.txt', 'w')
	players_file.write(json.dumps(atp_ids, indent=4, sort_keys=True))
	players_file.close()

def make_json_request(url):
	response_text = urlopen(url).read().decode('utf-8')
	return json.loads(response_text)

def get_player_stats(year, player_name):
	