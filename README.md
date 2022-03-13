# MediaWiki Tools

[![Coverage Status](https://coveralls.io/repos/github/nick-robo/MediaWiki-Tools/badge.svg?branch=main)](https://coveralls.io/github/nick-robo/MediaWiki-Tools?branch=main)

A high level library containing set of tools for for filtering pages using the rich data available in MediaWikis such as categories and info boxes. Uses both web-scraping and API methods (where available and feasible) to gather information.

# Goals

- Generate useful data (and datasets) from a wiki.
- To work on any MediaWiki (including `fandom.com`).
- Get arbitrary subsets of pages based on categories and template parameters.
- Be very robust to variations and inconsistencies in user input.
- Be efficient.
- Make available as a python package

# Installation

Through pip

```
pip install mediawiki-tools
```

# Usage

Create `MediaWikiTools` object:

```python
from mediawiki-tools import MediaWikiTools

mwt = MediaWikiTools('harrypotter.fandom.com')
mwt.has_api     # True
```

Get page names from a category.

```python
mwt.get_pages('1980_births')

#  ['Dudley Dursley',
#  'Neville Longbottom',
#  'Ernest Macmillan',
#  'Draco Malfoy',
#  'Harry Potter',
#  'Ronald Weasley']
```

Get an intersection of 2 or more categories.

```python
mwt.get_set(['1980_births', 'Hogwarts_dropouts'], operation='&')
# ['Harry Potter', 'Ronald Weasley']

mwt.get_set(['1980_births', 
             'Hogwarts_dropouts', 
             'Green-eyed_individuals'], 
            operation='intersection')
# ['Harry Potter']
```

Get a union of 2 or more categories.

```python
mwt = MediaWikiTools('en.wikipedia.org')

mwt.get_set(['Countries in Asia', 'Countries_in_Europe'],
	          operation='&')
# ['Cyprus',
#  'Pakistan',
#  'Croatia',
#   ...
#  'Belarus',
#  'Bangladesh',
#  'Lithuania']
```

Chaining operations.

```python
# get the intersection of countries in Europe and Asia and save it
countries = mwt.get_set(['Countries in Asia', 'Countries_in_Europe'],
	          operation='&')
# intersect the saved list with a different category
mwt.get_set('Russian-speaking_countries_and_territories', 
            operation='&', 
            pages_list=countries)
# ['Kyrgyzstan',
#  'Moldova',
#  'Russia',
#  'Armenia',
#  'Tajikistan',
#  'Belarus',
#  'Azerbaijan',
#  'Uzbekistan',
#  'Mongolia',
#  'Kazakhstan']
```