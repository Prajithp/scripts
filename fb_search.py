#!/usr/bin/python

import requests, os, sys
import re, json
from bs4 import BeautifulSoup, Comment

class Facebook():
	def __init__(self, **kwargs):

		self.username = kwargs.get('username')
		self.password = kwargs.get('password')

		self.base_url = "https://www.facebook.com"
		self.session = requests.Session()
		self.session.headers.update({
   			'User-Agent': 'Mozilla/5.0 (X11; Linux i686; rv:39.0) Gecko/20100101 Firefox/39.0'
		})
		

	def login(self):
		response = self.session.get(self.base_url)
		soup = BeautifulSoup(response.text, 'html.parser');
		action_url = soup.find('form', id='login_form')['action']
		inputs = soup.find('form', id='login_form').findAll('input', {'type': ['hidden', 'submit']})
		post_data = {input.get('name'): input.get('value')  for input in inputs}
	
		post_data['email'] = self.username
		post_data['pass'] = self.password

		response = self.session.post(action_url, data=post_data, allow_redirects=False);
		if response.status_code == 200:
			assert False, "[-] login failed"

		return True

	def search(self, keyword=None, companyid=None):
		search_url 	= self.base_url + "/search/people/?q={query}&ref=top_filter"
		if companyid is not None:
			search_url += "&filters_employer={id}"

		filters = {"name": "users_employer", "args": companyid}
		response   	= self.session.get(search_url.format(query=keyword, id=filters))
		soup       	= BeautifulSoup(response.text, 'html.parser')
		comments 	= soup.find_all(text=lambda text:isinstance(text, Comment))
		for comment in comments:
			soup = BeautifulSoup(comment, 'html.parser')
			container = soup.find('div', {"id": "BrowseResultsContainer"})
			if container:
				soup = BeautifulSoup(str(container), 'html.parser')
				peoples = soup.find_all('div', attrs={'class': '_32mo'})
				return peoples

		return None

	def get_emp_by_employer(self, companyid):
		accounts = {}
		keywords  = map(chr, range(ord('a'), ord('z')+1))
		for keyword in keywords:
			employees = self.search(keyword=keyword, companyid=companyid)
			if employees is not None:
				try:
					for account in employees:
						url = account.previous_element.get('href')
						accounts[account.text] = url
				except:
					pass
		return accounts


if __name__ == '__main__':
	cmp_id = sys.argv[1]
	facebook = Facebook(username="xxxxxx", password="xxxxxxxx")
	if facebook.login():
		accounts = facebook.get_emp_by_employer(companyid=cmp_id)
		for name, url in accounts.items():
			print("{} - {}".format(name, url))
	else:
		assert "login failed"
