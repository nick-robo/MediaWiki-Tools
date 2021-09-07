# %%
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, quote, unquote
import re
from typing import Union
from itertools import combinations
from warnings import warn
from mediawiki import MediaWiki
from pprint import pprint
# import mwparserfromhell as mwp


class WikiSubsetter:
	def __init__(self, input_url: str):
		"""Create WikiSubsetter object from a MediaWiki page.

		Args:
			input_url (str): A url from the wiki to be subsetted.
			Preferrably the main page or api.
		"""

		if input_url.strip() == '':
			raise ValueError('Empty wiki url')

		self.parsed_url = urlparse(input_url)

		if not self.parsed_url.scheme:
			self.parsed_url = urlparse('http://' + input_url)

		if not len(self.parsed_url.netloc.split(".")) > 1:
			raise ValueError(f'Invalid url: {input_url}')

		# get base url
		self.base_url = self.parsed_url._replace(path='',
		                                         params='',
		                                         fragment='').geturl()

		# get page name (wiki.com/page_name/Page) from input
		match = None
		if self.parsed_url.path:
			path = self.parsed_url.path.replace('/', '%')
			match = re.match('%(.*?)%', path)

		self.page_name = match.group(1) if match else None

		page = requests.get(self.base_url)
		if not page.ok:
			raise Exception(f"Couldn't conntect to {self.base_url}")

		# method 2: get page name from landing page
		if not self.page_name:
			path = urlparse(page.url).path.replace('/', '%')
			match = re.match('%(.*?)%', path)
			self.page_name = match.group(1) if match else None

		# method 3: search landing page for link to main page
		if not self.page_name:
			data = BeautifulSoup(page.text, 'html.parser')
			r = [
			    h for x in data.find_all('a')
			    if (h := x.get('href')) and 'Main' in h
			]
			self.page_name = r[0].split('/')[0] if r else None

		# method 4: last ditch attempt
		if not self.page_name:
			r = [
			    # find /page_name/Page links and get page_name
			    h[1] for x in data.find_all('a')
			    if (h := x.get('href')) and len(h := h.split('/')) == 3
			]
			# get most frequent page name
			self.page_name = max(set(r), key=r.count) if r else None

		# ensure page name was found
		assert self.page_name, 'Could not get page name\
								(wiki.com/page_name/Page)\n\
								Try input an article page'

		self.page_base_url = self.base_url + '/' + self.page_name + '/'

		# try to get api
		# build target list
		# TODO: Research more targets
		targets = [
		    input_url if 'api' in input_url else None,
		    self.base_url + '/wiki/api.php',
		    self.base_url + '/api.php',
		    self.base_url + '/w/api.php',
		    self.page_base_url + 'api.php',
		]

		for target in targets:
			# skip None
			if not target:
				continue

			# TODO: Find faster way than creating object
			try:
				self.mw = MediaWiki(target)
				self.api_url = target
				self.has_api = True
				break
			except Exception:
				continue
		else:
			self.mw = None
			self.has_api = False
			self.api_url = None
			warn('Could not find API, web scraping will be used')

	def __filter_pagelist(self, page_list: list[str], get_lists: bool,
	                      list_only: bool) -> list[str]:
		# TODO: Figure out better method to find lists

		filtered = []

		for page in page_list:
			if 'File:' in page:
				continue

			if get_lists:
				filtered.append(page)
			elif list_only and 'List ' in page:
				filtered.append(page)
			elif 'List ' not in page:
				filtered.append(page)

		return filtered

	def get_data(self,
	             input: str,
	             print_pretty: bool = False) -> BeautifulSoup:
		if 'http' in input:
			page = requests.get(input)
		else:
			# get fragment if incomplete url and url encode it
			input = quote(input.split('/')[-1].replace(' ', '_'))
			page = requests.get(self.page_base_url + 'Category:' + input)

			# if not category
			if not page.ok:
				page = requests.get(self.page_base_url + input)

		if not page.ok:
			raise Exception(f'Failed on page {page}')

		data = BeautifulSoup(page.text, 'html.parser')
		if print_pretty:
			print()
		return data

	def get_pages(self,
	              input_link: str,
	              get_subcats: bool = False,
	              with_subcats: bool = False,
	              get_lists: bool = False,
	              recursive: bool = False,
	              list_only: bool = False,
	              use_api: bool = True,
	              _base: bool = True) -> Union[list[str], dict]:
		"""Get the pages from a category or list of the wiki.

		Args:
			input_link (str): Url or name of category or list.

			get_subcats (bool, optional): If True, gets links from first \
				level subcategories. Defaults to False.

			get_lists (bool, optional): Gets lists in addition to pages. \
				Assumption (problematic): list has 'List_' in name \
				Defaults to False.

			recursive (bool, optional): Recursively get links from \
				subcategories. Defaults to False.

			list_only (bool, optional): Only get links that are lists. \
				Assumption (slightly risky, only no api): \
				Lists are on the first page. \
				Defaults to False.

			use_api (bool, optional): Whether to use the api (if present). \
				Defaults to true.

		Returns:
			list[str]: A list of pages.
		
		Note:
			API and non-API methods may return different results based on \
			how recently the category page was updated. API mehtod should \
			be considered correct.
		"""
		pages: Union[list[str], dict] = {} if with_subcats else []

		if self.has_api and use_api:
			cat_name = None

			if any([x in input_link for x in self.base_url.split('/') if x]):
				i = input_link.split('/').index(self.page_name)
				cat_name = '/'.join(input_link.split('/')[i + 1:])
				cat_name = cat_name.split(
				    ':', 1)[1] if 'Category:' in cat_name else cat_name

			cat_name = input_link if not cat_name else cat_name
			pages_res, subcats = self.mw.categorymembers(cat_name,
			                                             results=None)

			# add current category links to result
			pages_res = self.__filter_pagelist(pages_res,
			                                   get_lists=get_lists,
			                                   list_only=list_only)
			if with_subcats:
				pages['self'] = pages_res
			else:
				pages.extend(pages_res)

			# get subcategories
			if (get_subcats or recursive):
				for cat in subcats:
					pages_res = self.get_pages(cat,
					                           get_subcats=recursive,
					                           recursive=recursive,
					                           with_subcats=(recursive
					                                         and with_subcats),
					                           _base=False)
					if with_subcats:
						# filter each sublist
						pages[cat] = self.__filter_pagelist(
						    pages_res,
						    get_lists=get_lists,
						    list_only=list_only) if type(
						        pages_res) is not dict else pages_res
					else:
						pages.extend(pages_res)

			if not with_subcats:
				# filter pagelist once
				pages = self.__filter_pagelist(pages,
				                               get_lists=get_lists,
				                               list_only=list_only)

		# if no api available
		else:
			if any([x in self.base_url for x in ['wikia.', 'fandom.com']]):
				raise NotImplementedError(
				    'Web scraping not implemented for wikia/fandom.com')

			data = self.get_data(input_link)

			# get category name from input link
			cat_name = input_link.split(':')[-1].replace('_', ' ')

			# get page div if category
			content = data.find(id='mw-pages')
			# if category is title
			is_category = 'Category:' in data.find(id='firstHeading').text

			if is_category and not list_only:
				links = data.find_all('a')

				next_page = list(filter(lambda x: x.text == 'next page',
				                        links))

				# get pages from subcats
				if (get_subcats
				    or recursive) and (s := data.find(id='mw-subcategories')):
					for input_link in s.find_all('a'):
						if (h := input_link.get('href')) and 'Category' in h:
							pages_res = self.get_pages(
							    self.base_url + h,
							    get_subcats=recursive,
							    get_lists=get_lists,
							    recursive=recursive,
							    with_subcats=(with_subcats and recursive),
							    use_api=use_api,
							    _base=False)
							if with_subcats:
								subcat_name = input_link.text
								pages[input_link.text] = pages_res
							else:
								pages.extend(pages_res)

				links = [
				    link.text for link in content.find_all('a')
				    # check href not None and if it is a page link
				    if (h := link.get('href')) and self.page_name in h and
				    # filter lists if get_lists is false
				    (True if get_lists else 'List ' not in link.text)
				]

				if len(next_page) != 0:
					pages_res = self.get_pages(self.base_url +
					                           next_page[0].get('href'),
					                           get_lists=get_lists,
					                           use_api=use_api)

					links.extend(pages_res)

			# get lists only
			elif is_category and list_only:
				# assumption: all lists are on first page (>200 lists)
				links = [
				    h for x in content.find_all('a')
				    if (h := x.get('href')) and 'List_' in h
				]
			# if input_link is list
			else:
				content = data.find(id="mw-content-text").find_all('a')
				links = [
				    x.get('href') for x in content
				    if len(x) == 1 and not x.get('class')
				]

			if with_subcats:
				pages['self'] = links
			else:
				pages.extend(links)

		if recursive and _base and with_subcats:
			pages = {cat_name: pages}

		return pages

	def get_set(self,
	            categories: Union[list[str], str],
	            operation: str,
	            pages_list: list[str] = [],
	            get_subcats: bool = False,
	            use_lists: bool = False) -> list[str]:

		operation_dict = {
		    'intersection': 'intersection_update',
		    'i': 'intersection_update',
		    'and': 'intersection_update',
		    '&': 'intersection_update',
		    'union': 'update',
		    'u': 'update',
		    'or': 'update',
		    '|': 'update'
		}

		if operation not in operation_dict.keys():
			raise Exception(f"Invalid operation: {operation} \
				chose from following: \n\t{operation_dict.keys()}")

		page_set = set()
		operator = operation_dict[operation]

		# use lists to increase efficiency
		# caveat: slightly slower if list does not exist
		if use_lists and operation == 'intersection' and len(categories) > 1:
			combs = combinations(categories, 2)
			done = set()
			for comb in combs:
				# skip if both categories have been intersected
				if all([x in done for x in comb]):
					continue
				lists = self.get_pages(comb[0], list_only=True)
				# replace underscore and remove plural ([:-1])
				# assumption: categories are english
				s = comb[1].replace('_', ' ').lower()
				s = s[:-1] if s[-1] == 's' else s
				# match category string s in lists
				lists = [x for x in lists if s in x.lower().replace('_', ' ')]
				if lists:
					# if list is not empty get links from the first one
					# (should always be one result)
					list_pages = self.get_pages(lists[0])
					# if page_list is not empty, intersect
					if pages_list:
						pages_list = set(pages_list).intersection(list_pages)
					else:
						pages_list.extend(list_pages)
					# remove list items from categories
					done.update(comb)
			if len(done) == len(set(categories)):
				return list(pages_list)

		# edge cases
		if not categories:
			raise Exception('Invalid argument')
		elif len(categories) == 1:
			page_set.update(self.get_pages(categories[0]))
		elif type(categories) == str:
			page_set.update(self.get_pages(categories))
		else:
			for category in categories:
				if not page_set:
					page_set.update(self.get_pages(category, get_subcats))
					continue
				getattr(page_set,
				        operator)(self.get_pages(category, get_subcats))

		if pages_list:
			getattr(page_set, operator)(pages_list)

		return list(page_set)

	def get_info(pages: Union[list[str], str]):
		raise NotImplementedError()
		# parsed_wikitext = mwp.parse(wikitext)
		# get params dict from parsed template
		# p_dict = {(kv := p.split('=', 1))[
		#	 0].strip(): kv[1].strip() for p in biobox.params}


# %%

ws = WikiSubsetter('boobpedia.com')
cats = [
    'Europe',
    'Your_Mom',
    'https://en.uncyclopedia.co/wiki/Category:Your_Mom',
]

res_api = ws.get_pages(cats[0],
                       get_subcats=True,
                       with_subcats=True,
                       recursive=True,
                       use_api=True)

res_no_api = ws.get_pages(cats[0],
                          get_subcats=True,
                          recursive=True,
                          with_subcats=True,
                          use_api=False)
# %%
