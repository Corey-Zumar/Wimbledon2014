from bs4 import BeautifulSoup
from urllib.request import urlopen
from urllib.request import HTTPError
import urllib
import json
from datetime import datetime

def get_2014_round_one():
	draw = {}
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
	draw[1] = matches
	write_draw(2014, draw)

def update_2014_draw_with_stats(round):
	year = 2014
	players = {}
	draw = load_draw(year)
	curr_round = draw[str(round)]
	for match in curr_round:
		player_one = match['player_1']
		player_two = match['player_2']
		if player_one in players:
			match['player_1_prior_stats'] = players[player_one]
		else:
			player_one_stats = get_stats(player_one, year)
			players[player_one] = player_one_stats
			match['player_1_prior_stats'] = player_one_stats
		if player_two in players:
			match['player_2_prior_stats'] = players[player_two]
		else:
			player_two_stats = get_stats(player_two, year)
			players[player_two] = player_two_stats
			match['player_2_prior_stats'] = player_two_stats
	players = {}
	write_draw(year, draw)

def update_2014_draw_with_h2h(round, surface):
	ids_dict = json.loads(load_atp_ids_file())
	year = 2014
	draw = load_draw(year)
	curr_round = draw[str(round)]
	for match in curr_round:
		h2h = get_head_to_head(ids_dict, year, surface, match['player_1'], match['player_2'])
		if surface is None:
			match['player_1_h2h'] = h2h[0]
			match['player_2_h2h'] = h2h[1]
		else:
			match['player_1_h2h_' + surface] = h2h[0]
			match['player_2_h2h_' + surface] = h2h[1]
	write_draw(year, draw)

def update_2014_draw_with_rankings(round):
	year = 2014
	draw = load_draw(year)
	curr_round = draw[str(round)]
	for match in curr_round:
		player_one = match['player_1']
		player_two = match['player_2']
		player_one_ranking = get_ranking(player_one, year)
		match['player_1_ranking'] = player_one_ranking
		player_two_ranking = get_ranking(player_two, year)
		match['player_2_ranking'] = player_two_ranking
		write_draw(year, draw)

def get_draws(start_year, end_year):
	for i in range(start_year, end_year + 1):
		print('Getting draw for ' + str(i))
		write_draw(i, get_draw(i))

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

def get_most_accurate_h2h_year(surface):
	most_accurate_year = 0
	highest_accuracy = 0
	for year in range(1993, 2014):
		accuracy = get_h2h_prediction_accuracy(year, year, surface)
		if accuracy > highest_accuracy:
			highest_accuracy = accuracy
			most_accurate_year = year
	return 'Year: ' + str(most_accurate_year) + ' Accuracy: ' + str(highest_accuracy)

def get_least_accurate_h2h_year(surface):
	least_accurate_year = 0
	lowest_accuracy = 100
	for year in range(1993, 2014):
		accuracy = get_h2h_prediction_accuracy(year, year, surface)
		if accuracy < lowest_accuracy:
			lowest_accuracy = accuracy
			least_accurate_year = year
	return 'Year: ' + str(least_accurate_year) + ' Accuracy: ' + str(lowest_accuracy)

def get_h2h_prediction_accuracy(start_year, end_year, surface):
	matches = 0
	h2h_total = 0
	h2h_accurate = 0
	for year in range(start_year, end_year + 1):
		draw = load_draw(year)
		for i in range(1, 8):
			round = draw[str(i)]
			for match in round:
				matches += 1
				player_one = match['player_1']
				player_two = match['player_2']
				if surface is None:
					player_one_h2h = match['player_1_h2h']
					player_two_h2h = match['player_2_h2h']
				else:
					player_one_h2h = match['player_1_h2h_' + surface]
					player_two_h2h = match['player_2_h2h_' + surface]
				winner = match['winner']
				if player_one_h2h != player_two_h2h and (player_one_h2h > 0 or player_two_h2h) > 0:
					h2h_total += 1
					if player_one_h2h > player_two_h2h and winner == player_one or player_two_h2h > player_one_h2h and winner == player_two:
						h2h_accurate += 1

	print('Total matches: ' + str(matches))
	print('Total significant head-to-heads: ' + str(h2h_total))
	print('Percentage: ' + str(h2h_total / matches))
	print('Accurate head-to-heads: ' + str(h2h_accurate))
	print('Percentage: ' + str(h2h_accurate / h2h_total))
	return (h2h_accurate / h2h_total)

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



def update_draws_with_h2h(start_year, end_year, surface):
	ids_dict = json.loads(load_atp_ids_file())
	for year in range(start_year, end_year + 1):
		draw = load_draw(year)
		for i in range(1, 8):
			curr_round = draw[str(i)]
			for match in curr_round:
				h2h = get_head_to_head(ids_dict, year, surface, match['player_1'], match['player_2'])
				if surface is None:
					match['player_1_h2h'] = h2h[0]
					match['player_2_h2h'] = h2h[1]
				else:
					match['player_1_h2h_' + surface] = h2h[0]
					match['player_2_h2h_' + surface] = h2h[1]
		write_draw(year, draw)

surfaces = ['Hard', 'Clay', 'Grass', 'Carpet']
date_format = '%d.%m.%Y'

def get_head_to_head(ids_dict, year, surface, player_one, player_two):
	wimbledon_date = datetime.strptime('23.06.2014', date_format)
	tournaments_dict = load_tournaments_file()
	url = 'http://www.atpworldtour.com/Players/Head-To-Head.aspx?pId=' + ids_dict[player_one] + '&oId=' + ids_dict[player_two]
	print('Accessing ' + url)
	h2h_soup = get_soup(url)
	strongs = h2h_soup.find_all('strong')
	tournaments = []
	for link in h2h_soup.find_all('a'):
		if ('/Tennis/Tournaments/' in link['href'] or link['href'] == '#') and link.find('strong') != None:
			tournaments.append((link.text, link['href']))
	h2h_surfaces = []
	for td in h2h_soup.find_all('td'):
		if td.text in surfaces:
			h2h_surfaces.append(td.text)
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
		match_surface = h2h_surfaces[x]
		if (match_year < year or match_year == year and date < wimbledon_date) and (surface is None or match_surface == surface):
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
	round_one = draw[str(1)]
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

def update_draws_with_rankings(start_year, end_year):
	players = {}
	for year in range(start_year, end_year + 1):
		draw = load_draw(year)
		for i in range(1, 8):
			curr_round = draw[str(i)]
			for match in curr_round:
				player_one = match['player_1']
				player_two = match['player_2']
				if player_one in players:
					match['player_1_ranking'] = players[player_one]
				else:
					player_one_ranking = get_ranking(player_one, year)
					match['player_1_ranking'] = player_one_ranking
					players[player_one] = player_one_ranking
				if player_two in players:
					match['player_2_ranking'] = players[player_two]
				else:
					player_two_ranking = get_ranking(player_two, year)
					match['player_2_ranking'] = player_two_ranking
					players[player_two] = player_two_ranking
		players = {}
		write_draw(year, draw)

def get_ranking(player_name, year):
	wimbledon_date = datetime.strptime('23.06.' + str(year), date_format)
	first_letter = player_name[0]
	last_name = player_name[player_name.index(" ") + 1:]
	last_name_first_two_letters = last_name[:2]
	url = 'http://www.atpworldtour.com/Tennis/Players/' + last_name_first_two_letters + '/' + first_letter + '/' + urllib.parse.quote_plus(player_name.replace(" ", "-")) + '.aspx?t=rh&y=' + str(year)
	year
	ranking_soup = None
	try:
		ranking_soup = get_soup(url)
	except HTTPError as e:
		url = ''
		try:
			url = 'http://www.atpworldtour.com/Tennis/Players/Top-Players/' + player_name.replace(" ", "-") + '.aspx?t=rh&y=' + str(year) 
			ranking_soup = get_soup(url)
		except HTTPError:
			print('Failed: ' + url)
			return 'Unknown'
	print('Accessing ' + url)
	rank_pos = 0
	if ranking_soup is not None:
		rankings = ranking_soup.find_all('td')
		for i in range(0, len(rankings)):
			date_string = rankings[i]
			date_string_text = date_string.text
			if len(date_string_text) == 10:
				if datetime.strptime(date_string_text, date_format) <= wimbledon_date:
					return rankings[i + 1].text

def update_draws_with_stats(start_year, end_year):
	players = {}
	for year in range(start_year, end_year + 1):
		draw = load_draw(year)
		for i in range(1, 8):
			curr_round = draw[str(i)]
			for match in curr_round:
				player_one = match['player_1']
				player_two = match['player_2']
				if player_one in players:
					match['player_1_prior_stats'] = players[player_one]
				else:
					player_one_stats = get_stats(player_one, year)
					players[player_one] = player_one_stats
					match['player_1_prior_stats'] = player_one_stats
				if player_two in players:
					match['player_2_prior_stats'] = players[player_two]
				else:
					player_two_stats = get_stats(player_two, year)
					players[player_two] = player_two_stats
					match['player_2_prior_stats'] = player_two_stats
		players = {}
		write_draw(year, draw)

def get_stats(player_name, year):
	stats = {}
	first_letter = player_name[0]
	last_name = player_name[player_name.index(" ") + 1:]
	last_name_first_two_letters = last_name[:2]
	url = 'http://www.atpworldtour.com/Tennis/Players/' + last_name_first_two_letters + '/' + first_letter + '/' + urllib.parse.quote_plus(player_name.replace(" ", "-")) + '.aspx?t=mf&y=' + str(year)
	stats_soup = None
	try:
		stats_soup = get_soup(url)
	except HTTPError:
		try:
			url = 'http://www.atpworldtour.com/Tennis/Players/Top-Players/' + player_name.replace(" ", "-") + '.aspx?t=mf&y=' + str(year) 
			stats_soup = get_soup(url)
		except HTTPError:
			print('Failed: ' + url)

	if stats_soup is not None:
		print('Accessing ' + url)
		for title in stats_soup.find_all('li'):
			try:
				stat = title.find('span').text
				if len(stat) < 5 and len(stat) > 0 and ":" not in stat:
					stat_title = title.text[len(stat):]
					stats[stat_title] = stat
			except Exception:
				continue
	return stats

def determine_ranking_distance_win_percentage(distance, start_year, end_year):
	ranking_correct = 0
	match_total = 0
	for year in range(start_year, end_year + 1):
		draw = load_draw(year)
		for i in range(1, 8):
			round = draw[str(i)]
			for match in round:
				player_one = match['player_1']
				player_two = match['player_2']
				player_one_ranking = match['player_1_ranking']
				player_two_ranking = match['player_2_ranking']
				player_one_ranking = player_one_ranking.replace(",", "")
				player_two_ranking = player_two_ranking.replace(",", "")
				if 'T' in player_one_ranking:
					player_one_ranking = player_one_ranking[:len(player_one_ranking) - 1]
				if 'T' in player_two_ranking:
					player_two_ranking = player_two_ranking[:len(player_two_ranking) - 1]
				if player_one_ranking != 'Unknown' and player_two_ranking != 'Unknown' and len(player_one_ranking) > 0 and len(player_two_ranking) > 0:
					player_one_ranking = int(player_one_ranking)
					player_two_ranking = int(player_two_ranking)
					winner = match['winner']
					difference = abs(player_one_ranking - player_two_ranking)
					upper_threshold = distance + (distance * .2)
					if distance < 20:
						upper_threshold = 5
					if difference > distance and difference < upper_threshold:
						match_total += 1
						if (player_one_ranking < player_two_ranking and winner == player_one) or (player_two_ranking < player_one_ranking and winner == player_two):
							ranking_correct += 1
	#print('Total matches: ' + str(match_total))
	#print(distance + (distance * .2))
	try:
		return str(ranking_correct / match_total)
	except Exception:
		return 'N/A'



def get_average_ranking_distance(start_year, end_year):
	ranking_correct = 0
	match_total = 0
	total_distance = 0
	for year in range(start_year, end_year + 1):
		draw = load_draw(year)
		for i in range(1, 8):
			round = draw[str(i)]
			for match in round:
				player_one = match['player_1']
				player_two = match['player_2']
				player_one_ranking = match['player_1_ranking']
				player_two_ranking = match['player_2_ranking']
				player_one_ranking = player_one_ranking.replace(",", "")
				player_two_ranking = player_two_ranking.replace(",", "")
				if 'T' in player_one_ranking:
					player_one_ranking = player_one_ranking[:len(player_one_ranking) - 1]
				if 'T' in player_two_ranking:
					player_two_ranking = player_two_ranking[:len(player_two_ranking) - 1]
				if player_one_ranking != 'Unknown' and player_two_ranking != 'Unknown' and len(player_one_ranking) > 0 and len(player_two_ranking) > 0:
					player_one_ranking = int(player_one_ranking)
					player_two_ranking = int(player_two_ranking)
					match_total += 1
					winner = match['winner']
					total_distance += abs(player_one_ranking - player_two_ranking)
					if (player_one_ranking < player_two_ranking and winner == player_one) or (player_two_ranking < player_one_ranking and winner == player_two):
						ranking_correct += 1
	print('Total matches: ' + str(match_total))
	print('Ranking correct total: ' + str(ranking_correct))
	print('Percentage: ' + str(ranking_correct / match_total))
	print('Average distance: ' + str(total_distance / match_total))

def get_accuracy(distance, start_year, end_year, percentage, statname):
	match_total = 0
	correct = 0
	for year in range(start_year, end_year + 1):
		draw = load_draw(year)
		for i in range(1, 8):
			round = draw[str(i)]
			for match in round:
				player_one = match['player_1']
				player_two = match['player_2']
				winner = match['winner']
				player_one_stats = match['player_1_prior_stats']
				player_two_stats = match['player_2_prior_stats']
				if len(player_one_stats) > 0 and len(player_two_stats) > 0:
					player_one_stat = player_one_stats[statname]
					player_two_stat = player_two_stats[statname]
					if percentage:
						player_one_stat = int(player_one_stat[0:len(player_one_stat) - 1])
						player_two_stat = int(player_two_stat[0:len(player_two_stat) - 1])
					else:
						player_one_stat = int(player_one_stat)
						player_two_stat = int(player_two_stat)
					if distance is not None:
						difference = abs(player_one_stat - player_two_stat)
					if distance is None or (difference > distance and difference < distance + 2):
						match_total += 1
						if (player_one_stat > player_two_stat and winner == player_one) \
						or (player_two_stat > player_one_stat and winner == player_two):
							correct += 1
	#print('Total matches: ' + str(match_total))
	#print('Correct ' + statname + ' total: ' + str(correct))
	try:
		return str(correct / match_total)
	except Exception:
		return 'N/A'

def compare_players(player_one_input, player_two_input):
	year = 2014
	draw = load_draw(year)
	round = draw[str(1)]
	player_one = None
	player_two = None
	for match in round:
		if match['player_1'] == player_one_input:
			player_one = match['player_1']
			player_one_stats = match['player_1_prior_stats']
			player_one_h2h = match['player_1_h2h']
			player_one_ranking = match['player_1_ranking']
			player_one_first_serve_pts_won = player_one_stats['1st Serve Points Won']
			player_one_second_serve_pts_won = player_one_stats['2nd Serve Points Won']
			player_one_service_pts_won = player_one_stats['Service Points Won']
			player_one_total_pts_won = player_one_stats['Total Points Won']

		if match['player_2'] == player_one_input:
			player_one = match['player_2']
			player_one_stats = match['player_2_prior_stats']
			player_one_h2h = match['player_2_h2h']
			player_one_ranking = match['player_2_ranking']
			player_one_first_serve_pts_won = player_one_stats['1st Serve Points Won']
			player_one_second_serve_pts_won = player_one_stats['2nd Serve Points Won']
			player_one_service_pts_won = player_one_stats['Service Points Won']
			player_one_total_pts_won = player_one_stats['Total Points Won']

		if match['player_1'] == player_two_input:
			player_two = match['player_1']
			player_two_stats = match['player_1_prior_stats']
			player_two_h2h = match['player_1_h2h']
			player_two_ranking = match['player_1_ranking']
			player_two_first_serve_pts_won = player_two_stats['1st Serve Points Won']
			player_two_second_serve_pts_won = player_two_stats['2nd Serve Points Won']
			player_two_service_pts_won = player_two_stats['Service Points Won']
			player_two_total_pts_won = player_two_stats['Total Points Won']

		if match['player_2'] == player_two_input:
			player_two = match['player_2']
			player_two_stats = match['player_2_prior_stats']
			player_two_h2h = match['player_2_h2h']
			player_two_ranking = match['player_2_ranking']
			player_two_first_serve_pts_won = player_two_stats['1st Serve Points Won']
			player_two_second_serve_pts_won = player_two_stats['2nd Serve Points Won']
			player_two_service_pts_won = player_two_stats['Service Points Won']
			player_two_total_pts_won = player_two_stats['Total Points Won']

		if player_one is not None and player_two is not None:
			h2hs = get_head_to_head(json.loads(load_atp_ids_file()), year, None, player_one, player_two)
			player_one_h2h = h2hs[0]
			player_two_h2h = h2hs[1]

			print('---- ' + player_one + ' ----')
			print('Ranking: ' + player_one_ranking)
			print('Head-To-Head: ' + str(player_one_h2h))
			print('First Serve Points Won: ' + str(player_one_first_serve_pts_won))
			print('Second Serve Points Won: ' + str(player_one_second_serve_pts_won))
			print('Service Points Won: ' + str(player_one_service_pts_won))
			print('Total Points Won: ' + str(player_one_total_pts_won))
			print('----------------------------')

			print('---- ' + player_two + ' ----')
			print('Ranking: ' + player_two_ranking)
			print('Head-To-Head: ' + str(player_two_h2h))
			print('First Serve Points Won: ' + str(player_two_first_serve_pts_won))
			print('Second Serve Points Won: ' + str(player_two_second_serve_pts_won))
			print('Service Points Won: ' + str(player_two_service_pts_won))
			print('Total Points Won: ' + str(player_two_total_pts_won))
			print('----------------------------')

			player_one_ranking = player_one_ranking.replace(",", "")
			player_two_ranking = player_two_ranking.replace(",", "")
			if 'T' in player_one_ranking:
				player_one_ranking = player_one_ranking[:len(player_one_ranking) - 1]
			if 'T' in player_two_ranking:
				player_two_ranking = player_two_ranking[:len(player_two_ranking) - 1]
			player_one_ranking = int(player_one_ranking)
			player_two_ranking = int(player_two_ranking)

			ranking_advantage = ''
			ranking_odds = determine_ranking_distance_win_percentage(abs(player_one_ranking - player_two_ranking), 1993, 2013)
			if player_one_ranking < player_two_ranking:
				ranking_advantage = player_one
			elif player_two_ranking > player_one_ranking:
				ranking_advantage = player_two
			else:
				ranking_advantage = 'None'

			player_one_second_serve_pts_won = int(player_one_second_serve_pts_won[0:len(player_one_second_serve_pts_won) - 1])
			player_two_second_serve_pts_won = int(player_two_second_serve_pts_won[0:len(player_two_second_serve_pts_won) - 1])

			second_serve_pts_odds = get_accuracy(abs(player_one_second_serve_pts_won - player_two_second_serve_pts_won), 1993, 2013, True, '2nd Serve Points Won')
			second_serve_advantage = ''
			if player_one_second_serve_pts_won > player_two_second_serve_pts_won:
				second_serve_advantage = player_one
			elif player_two_second_serve_pts_won > player_one_second_serve_pts_won:
				second_serve_advantage = player_two
			else:
				second_serve_advantage = 'None'

			player_one_first_serve_pts_won = int(player_one_first_serve_pts_won[0:len(player_one_first_serve_pts_won) - 1])
			player_two_first_serve_pts_won = int(player_two_first_serve_pts_won[0:len(player_two_first_serve_pts_won) - 1])

			first_serve_pts_odds = get_accuracy(abs(player_one_first_serve_pts_won - player_two_first_serve_pts_won), 1993, 2013, True, '1st Serve Points Won')
			first_serve_advantage = ''
			if player_one_first_serve_pts_won > player_two_first_serve_pts_won:
				first_serve_advantage = player_one
			elif player_two_first_serve_pts_won > player_one_first_serve_pts_won:
				first_serve_advantage = player_two
			else:
				first_serve_advantage = 'None'

			player_one_service_pts_won = int(player_one_service_pts_won[0:len(player_one_service_pts_won) - 1])
			player_two_service_pts_won = int(player_two_service_pts_won[0:len(player_two_service_pts_won) - 1])

			service_pts_odds = get_accuracy(abs(player_one_service_pts_won - player_two_service_pts_won), 1993, 2013, True, 'Service Points Won')
			service_advantage = ''
			if player_one_service_pts_won > player_two_service_pts_won:
				service_advantage = player_one
			elif player_one_service_pts_won > player_one_service_pts_won:
				service_advantage = player_two
			else:
				service_advantage = 'None'

			player_one_total_pts_won = int(player_one_total_pts_won[0:len(player_one_total_pts_won) - 1])
			player_two_total_pts_won = int(player_two_total_pts_won[0:len(player_two_total_pts_won) - 1])

			total_pts_odds = get_accuracy(abs(player_one_total_pts_won - player_two_total_pts_won), 1993, 2013, True, 'Total Points Won')
			total_advantage = ''
			if player_one_total_pts_won > player_two_total_pts_won:
				total_advantage = player_one
			elif player_two_total_pts_won > player_one_total_pts_won:
				total_advantage = player_two
			else:
				total_advantage = 'None'

			print('----------------------------')
			print('Ranking Advantage: ' + ranking_advantage + " " + ranking_odds)
			print('First Serve Points Won Advantage: ' + first_serve_advantage + " " + first_serve_pts_odds)
			print('Second Serve Points Won Advantage: ' + second_serve_advantage + " " + second_serve_pts_odds)
			print('Total Points Won Advantage: ' + total_advantage + " " + total_pts_odds)
			print('----------------------------')


			break

