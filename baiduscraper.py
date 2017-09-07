import urllib
import pandas as pd
import os
import datetime
import re
from tqdm import tqdm
from bs4 import BeautifulSoup as bs

class baidu:
	def __init__(self, baseURL, searchWord):
		self.baseURL = baseURL
		self.searchWord = searchWord
		self.searchArg = '/search?&word='+searchWord
		self.searchURL = urllib.parse.quote(self.baseURL+self.searchArg, safe='/:?=%&')

	def getPage(self, pageNum):
		try:
			url = self.searchURL+'&pn='+str(pageNum)
			response = urllib.request.urlopen(url)
			soup = bs(response, 'html.parser')
			return soup
		except Exception as e:
			if hasattr(e, 'reason'):
				print ('Cannot connect to baidu zhidao', e.reason)
				return None

	def getAnswerUrl(self, 
					 nb_results:'number of results to be returned'=10):
		#get all url on search results leading to answer page
		nb_iteration = 1 if nb_results<=10 else int(nb_results/10)+1
		results = []
		for i in range(nb_iteration):
			pageNum = i*10
			searchPage = self.getPage(pageNum)
			dt_tags = searchPage.find_all('dt')
			for tag in dt_tags:
				fetched_url = tag.find_next('a').get('href')
				if self.baseURL in fetched_url:	
					results.append(fetched_url)

		return results[:nb_results]

class ZDanswer:
	def __init__(self, url):
		self.url = url
		self.html_doc = bs(urllib.request.urlopen(self.url), 'html.parser')
		self.html_prettify = self.html_doc.prettify()
		self.title = self.getTitle()

	def getTitle(self):
		title = self.html_doc.title.text
		title = title.split('_')[0]
		return title

	def getDescription(self):
		desc_tag = self.html_doc.find_all(attrs={'name':'description'})
		content = desc_tag[0].get('content')
		return content

	def getAnswers(self, 
				   fetch_all:'return top answer if False'=True):
		try:
			best_answer = self.html_doc.find('pre').text
		except:
			best_answer = ''
		user_ans_tag = self.html_doc.find_all('span', 'con')

		all_answer = [best_answer] if best_answer!='' else []
		if fetch_all:
			for answer_tag in user_ans_tag:
				if answer_tag.parent.get('accuse') == 'aContent':
					answer = answer_tag.text.strip()
					all_answer.append(answer)
				else:
					pass
		
		return all_answer

def scraper(keywords=[], nb_pages_per_word=10):
	#given a list of keywords, number of answer pages to scrap for each word
	#return all the scrap comments relating to each keyword

	if type(keywords) == str:
		keywords = [keywords]

	baseURL = 'http://zhidao.baidu.com/' #the base url is not secured
	keywords = [kw.replace(' ', "%20") for kw in keywords]

	result_columns = ['url', 'keyword', 'title', 'descrption', 'answer']
	results = []

	for kw in keywords:
		searchEngine = baidu(baseURL, kw)
		ansUrlList = searchEngine.getAnswerUrl(nb_pages_per_word)
		for url in ansUrlList:
			ansPage = ZDanswer(url)

			print ('Fetching answers from '+ansPage.getTitle())

			for ans in ansPage.getAnswers():
				attributes = [url, kw, ansPage.getTitle(), ansPage.getDescription(), ans]
				results.append(attributes)
	df = pd.DataFrame(results, columns=result_columns)

	return df

def timenow():
	dt = datetime.datetime.now()
	sep = re.sub(r"[\s:-]", '', str(dt))
	tn = sep.split('.')[0]
	return tn

def save2dir(df, directory):
	if os.path.exists(directory):
		tn = timenow()
		df.to_excel(directory+tn+'.xlsx')
	else:
		os.mkdir(directory)
		df.to_excel(directory+tn+'xlsx')

if __name__ == '__main__':
	print ('Scrapper reads the keywords from a txt file, make sure the txt is in the same directory as this scrapper')

	with open('keywords.txt', 'r') as f:
		keywords = [x.strip() for x in f.readlines()]

	df = scraper(keywords)
	save2dir(df, 'results/')

	print ('Done')
