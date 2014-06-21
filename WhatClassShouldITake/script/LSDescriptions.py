from bs4 import BeautifulSoup
from urllib.request import urlopen
from urllib.request import HTTPError
import json

def pullLS():
	info_dict = {}
	ls_soup = getLSSoup()
	for link in ls_soup.find_all('a'):
		href_link = link.get('href')
		try:
			if 'major/' in href_link and len(href_link) <= 25 and 'major/major' not in href_link and 'contact.html' not in href_link:
				print(href_link)
				major_info = visitMajorURL(href_link)
				info_dict[major_info[0]] = {major_info[1] : major_info[2]}
		except TypeError:
			continue
	info_file = open('major_info.txt', 'w')
	info_file.write(json.dumps(info_dict, indent=4, sort_keys=True))
	info_file.close()
	return info_dict

def getLSSoup():
	ls_url = 'http://ls-advise.berkeley.edu/major/majorlist.html'
	return getSoup(ls_url)

def visitMajorURL(link):
	info = []
	related = []
	base_link = 'http://ls-advise.berkeley.edu/';
	major_soup = getSoup(base_link + link)
	major_title = major_soup.find('h1', {'class' : 'title'})
	info.append(major_title.text)
	main_content = major_soup.find('div', {'class' : 'content'})
	description = main_content.find('p')
	info.append(description.text)
	related_classes = major_soup.find('div', {'class' : 'related'})
	for related_class in related_classes.find_all('li'):
		related.append(related_class.text)
	info.append(related)
	return info

def pullCourses():
	major_info = pullLS()
	courses_map = {}
	for key in major_info.keys():
		courses_map[key] = getCourses(key)
	info_file = open('courses_info.txt', 'w')
	info_file.write(json.dumps(courses_map, indent=4, sort_keys=True))


def getSoup(link):
	page = urlopen(link)
	source = page.read()
	page.close()
	return BeautifulSoup(source)

def getCourses(major):
	courses = []
	courses_url = getCoursesUrl(major)
	courses_soup = getSoup(courses_url)
	titles = courses_soup.find_all('font', {'class' : 'coursetitle'})
	sections = courses_soup.find_all('font', {'size' : '2'})
	index = 0
	for section in sections:
		try:
			if section['color'] == '#000088':
				courses.append({section.text : titles[index].text})
				index += 1
		except KeyError:
			index += 1 
	return courses


def getCoursesUrl(major):
	major = major.replace(" ", "+")
	base_url_first = "http://osoc.berkeley.edu/OSOC/osoc?p_term=FL&x=34&p_classif=L&p_deptname="
	base_url_second = "&p_presuf=--+Choose+a+Course+Prefix%2fSuffix+--&y=6"
	full_url = base_url_first + major + base_url_second
	print(full_url)
	return full_url

def getBreadths():
	base_url = 'http://ls-advise.berkeley.edu/requirement/7breadth.html'
	breadth_soup = getSoup(base_url)
	content_area = breadth_soup.find('div', {'class' : 'content'})
	first_list = content_area.find('ul')
	for list_item in first_list.findAll('li'):
		link = list_item.find('a')
		breadth_link = link.get('href')
		getBreadthCourses(breadth_link)

def getBreadthCourses(link):
	breadth_courses = []
	base_url = 'http://ls-advise.berkeley.edu/'
	courses_soup = getSoup(base_url + link)
	content_area = courses_soup.find('div', {'class' : 'content'})
	first_list = content_area.find('ul')
	for course in first_list.findAll('li'):
		breadth_courses.append(course.text)
	breadth_info_file = open('breadth_info.txt', 'w')
	breadth_info_file.write(json.dumps(breadth_courses, indent=4, sort_keys=True))





