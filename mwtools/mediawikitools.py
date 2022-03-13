"""MediaWikiTools class module."""
# %%
import requests
from bs4 import BeautifulSoup
from bs4.element import PageElement
from urllib.parse import urlparse, quote
import re
from typing import Union
from warnings import warn
from mediawiki import MediaWiki
# from pprint import pprint
# import mwparserfromhell as mwp


class MediaWikiTools:
	"""MediaWikiTools object of a MediaWiki page.

	Args:
		input_url (str): A url from the wiki to be subsetted. Preferrably, the main
			page or API of the wiki.
	"""

	def __init__(self, input_url: str):
		"""Create MediaWikiTools instance."""
		# TODO: fails on input wikipedia.org (without en.)
		# TODO: check if input is a MediaWiki...
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
			match = re.search('%(.*?)%', path)
		self.page_name = match.group(1) if match else None

		page = requests.get(self.base_url)
		if not page.ok:
			raise Exception(f"Couldn't connect to {self.base_url}")

		# method 2: get page name from landing page
		if not self.page_name:
			path = urlparse(page.url).path.replace('/', '%')
			match = re.search('%(.*?)%', path)
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

	def _filter_page(self, page: Union[str, PageElement], get_lists: bool,
	                 list_only: bool) -> bool:
		# TODO: Add flexible filter list with regex
		# TODO Figure out a better way to deal with lists
		filter_words = ['File:']

		if issubclass(type(page), PageElement):
			# check href not None and if it is a page link
			if not (h := page.get('href')) or self.page_name not in h:
				return False

			name = page.text
			# wikipedia learn more
			if name == 'learn more':
				return False
		else:
			name = page

		if 'User:' in name:
			# Get data fails on user pages
			data = self.get_data(name)
			wip_box = data.find(class_='ombox-notice')
			if wip_box:
				ombox_text = wip_box.find(class_='mbox-text').text
				if 'work-in-progress' in ombox_text:
					return False

		if any(word in name for word in filter_words):
			return False
		elif get_lists and not list_only:
			return True
		elif list_only:
			return True if 'List ' in name else False
		elif 'List ' in name:
			return False
		else:
			return True

	def get_data(self,
	             input_page: str,
	             print_pretty: bool = False) -> BeautifulSoup:
		"""Get BeautifulSoup page data from category name or url.

		Args:
				input (str): Category name or url.
				print_pretty (bool, optional): Pretty print data for debuging. Defaults to
					False.

		Raises:
				Exception: If request fails.

		Returns:
				BeautifulSoup: BeautifulSoup object of input page.
		"""
		if 'http' in input_page:
			page = requests.get(input_page)
		else:
			# attempt to get namespace
			namespace = re.search(r'([A-Z]\w+)(:)', input_page)
			namespace = namespace.group(1) if namespace else None

			# use ':' for RE search
			if namespace:
				match = re.search(r'([:])(.+)', input_page)
				input_page = quote(match.group(2).replace(' ', '_'))
			else:
				# get fragment if incomplete url and url encode it
				match = re.search(r'([A-Z].+)', input_page)
				if not match:
					raise ValueError(f'Invalid input: {input_page}')
				input_page = quote(match.group(1).replace(' ', '_'))

			if namespace:
				page = requests.get(self.page_base_url + namespace + ':' +
				                    input_page)
			else:
				page = requests.get(self.page_base_url + 'Category:' +
				                    input_page)

			# if not category
			if not page.ok:
				page = requests.get(self.page_base_url + input_page)

		if not page.ok:
			raise Exception(f'Failed on page {page}')

		data = BeautifulSoup(page.text, 'html.parser')

		if print_pretty:
			print(data.prettify())

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
		r"""Get the pages from a category or list of the wiki.

		Args:
			input_link (str): Url or name of category or list.

			get_subcats (bool, optional): If True, gets links from first level
				subcategories. Defaults to False.

			with_subcats (bool, optional): Return dict of categories and
				corresponding pages.

			get_lists (bool, optional): Gets lists in addition to pages.
				Assumes (problematic) lists have `'List_'` in their name.
				Defaults to False.

			recursive (bool, optional): Recursively get links from
				subcategories. Defaults to False.

			list_only (bool, optional): Only get links that are lists.
				Assumes (slightly risky, only no api) that all lists are on the first page.
				Defaults to False.

			use_api (bool, optional): Whether to use the api (if present).
				Defaults to true.

		Returns:
			list[str] or dict: A list of pages.
		
		Note:
			API and non-API methods may return different results based on
				how recently the category/list page was updated. API mehtod
				should be considered correct.
		Note:
			If recursive and with_subcats the function with return a nested
				dictionary.
		"""
		pages: Union[list[str], dict] = {} if with_subcats else []

		if self.has_api and use_api:
			cat_name = None

			if any(x in input_link for x in self.base_url.split('/') if x):
				i = input_link.split('/').index(self.page_name)
				cat_name = '/'.join(input_link.split('/')[i + 1:])
				cat_name = cat_name.split(
				    ':', 1)[1] if 'Category:' in cat_name else cat_name

			cat_name = input_link if not cat_name else cat_name
			pages_res, subcats = self.mw.categorymembers(cat_name,
			                                             results=None)

			# add current category links to result
			pages_res = [
			    page for page in pages_res if self._filter_page(
			        page, get_lists=get_lists, list_only=list_only)
			]
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
						# filter each sublist if they are not dicts
						pages[cat] = [
						    page for page in pages_res if self._filter_page(
						        page, get_lists=get_lists, list_only=list_only)
						] if not type(pages_res) == dict else pages_res
					else:
						pages.extend(pages_res)

			if not with_subcats:
				# filter pagelist once
				pages = [
				    page for page in pages if self._filter_page(
				        page, get_lists=get_lists, list_only=list_only)
				]

		# if no api available
		else:
			if any(x in self.base_url for x in ['wikia.', 'fandom.com']):
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
								pages[input_link.text] = pages_res
							else:
								pages.extend(pages_res)

				links = [
				    link.text for link in content.find_all('a')
				    if self._filter_page(link, get_lists, list_only)
				] if content else []

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
				    link.text for link in content.find_all('a')
				    if self._filter_page(link, get_lists, list_only)
				]
			# if input_link is a List
			else:
				raise NotImplementedError('This is broken')
				content = data.find(id="mw-content-text")
				links = [
				    link.text for link in content.find_all('a')
				    if len(link) == 1 and not link.get('class')
				]

			if with_subcats:
				pages['self'] = links
			else:
				pages.extend(links)

		if recursive and _base and with_subcats:
			pages = {cat_name: pages}

		return pages

	def get_set(self,
	            categories: Union[list, str],
	            operations: Union[list[str], str],
	            pages_list: list[str] = None,
	            get_subcats: bool = False,
	            use_api: bool = True) -> list[str]:
		"""Get a subset (or superset) of pages.

		Args:
				categories (Union[list, str]): String or list of category names (or lists)
					operation (str): Intersection ('intersection', 'i', 'and', '&') or union
					('union', 'u', 'or', '|')
				
				operations (Union[list[str], str]): A single operation or
					`len(categories)-1` operations to apply to categories

				pages_list (list[str], optional): List of page to merge with queried ones
					using selected operation. Always last in order of operations. Defaults
					to None. (Obsolete)

				get_subcats (bool, optional): Get pages first level subcategories. Defaults
					to False.
				use_api (bool, optional): Use the MediaWiki API if available. Defaults to
					True.

		Returns:
				list[str]: List of pages resulting from the operations requested.

		Note:
			Set difference is not commutative. `categories` defines the order
				of operations
		"""
		operation_dict = {
		    'intersection': 'intersection_update',
		    'i': 'intersection_update',
		    'and': 'intersection_update',
		    '&': 'intersection_update',
		    'union': 'update',
		    'u': 'update',
		    'or': 'update',
		    '|': 'update',
		    'not': 'difference_update',
		    'difference': 'difference_update'
		}

		page_set = set()

		# check if all the operations are valid
		if not all(
		    map(lambda x: x in operation_dict,
		        operations if type(operations) == list else [operations])):
			raise Exception(f"Invalid operation: {operations} \
				chose from following: \n\t{operation_dict.keys()}")

		if type(operations) == list:
			# the first operation is always a union
			operations = ['u'] + operations
			# check that the number of inputs equals the number of operations
			assert (len(categories) + bool(pages_list)) == len(operations)
			operators = []
			for o in operations:
				operators.append(operation_dict[o])
		else:
			operators = [operation_dict[operations]
			             ] * (len(categories) + bool(pages_list))
			operators[0] = 'update'

		# edge cases
		if not categories:
			raise Exception('Invalid argument')
		elif len(categories) == 1:
			page_set.update(self.get_pages(categories[0], use_api=use_api))
		elif type(categories) == str:
			page_set.update(self.get_pages(categories, use_api=use_api))
		else:
			for category, operator in zip(categories, operators):
				getattr(page_set, operator)(
				    category if type(category) == list else self.
				    get_pages(category, get_subcats, use_api=use_api))

		if pages_list:
			getattr(page_set, operators[-1])(pages_list)

		return list(page_set)

	def get_info(self, pages: Union[list[str], str]):
		"""Not yet implemented.

		Args:
				pages (Union[list[str], str]): [description]

		Raises:
				NotImplementedError: [description]
		"""
		raise NotImplementedError()
		# parsed_wikitext = mwp.parse(wikitext)
		# get params dict from parsed template
		# p_dict = {
		# (kv := p.split('=', 1))[0].strip(): kv[1].strip() for p in biobox.params}


# %%
