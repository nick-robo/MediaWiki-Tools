"""MediaWikiTools class module.

# MediaWiki Tools

A high level library containing set of tools for for filtering pages using the
rich data available in MediaWikis such as categories and info boxes. Uses both
web-scraping and API methods (where available and feasible) to gather
information.

# Basic Usage

Create `MediaWikiTools` object:

```python
from mwtools import MediaWikiTools

hp_wiki = MediaWikiTools('harrypotter.fandom.com')
hp_wiki.has_api     # True
```

## Getting pages

Get page names from a category.

```python
hp_wiki.get_pages('1980_births')

#  ['Dudley Dursley',
#  'Neville Longbottom',
#  'Ernest Macmillan',
#  'Draco Malfoy',
#  'Harry Potter',
#  'Ronald Weasley']
```

Get pages from subcategories too.

```python
wiki = MediaWikiTools('en.wikipedia.org')

# get pages from category that contains only subcategories
wiki.get_pages("Art_collectors_by_nationality")
# []

# get pages from first level subcategories
wiki.get_pages("Art_collectors_by_nationality", get_subcats=True)
# ['William Hayes Ackland',
#  'William Acquavella',
#  'Frederick Baldwin Adams Jr.',
#  'Marella Agnelli',
#  'Robert Agostinelli',
#  ...]
```

Recursively get pages from subcategories. This can be quite slow for deep
subcategory trees and may break if loops are present.

```python
wiki.get_pages("Art_collectors_by_nationality", 
               get_subcats=True,
               recursive=True)
# ['Very',
#  'Long,
#  'List']
```

Get pages from subcategories as a dictionary containing subcategories as keys.
`'self'` contains the pages in the root category. Using `recursive` in
combination with the `with_subcats` results in a nested dictionary.

```python
# get first level subcats in dict
wiki.get_pages("Art_collectors_by_nationality", 
               get_subcats=True, with_subcats=True)
# {'self': [],
#  'American art collectors': ['William Hayes Ackland',
#                              'William Acquavella',
#                              'Frederick Baldwin Adams Jr.',
#                              ...],
#   ...
#  'Venezuelan art collectors': ['Gustavo Cisneros',
#                                'Patricia Phelps de Cisneros',
#                                'Nina Fuentes'],
#  'Yugoslav art collectors': ['Antun Bauer (museologist)', 'Erich Šlomović']}
```

## Getting sets

Get an intersection of 2 or more categories.

```python
hp_wiki.get_set(['1980_births', 'Hogwarts_dropouts'], operations='&')
# ['Harry Potter', 'Ronald Weasley']

hp_wiki.get_set(['1980_births',
                'Hogwarts_dropouts',
                'Green-eyed_individuals'],
                operations='intersection')
# ['Harry Potter']
```

Get a union of 2 or more categories.

```python
wiki = MediaWikiTools('en.wikipedia.org')

# get the union of countries in Europe and Asia and save it
countries = wiki.get_set(['Countries in Asia', 'Countries_in_Europe'],
	           operations='or')
print(countries)
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
# intersect the saved list with a different category
wiki.get_set(['Russian-speaking_countries_and_territories', countries], 
             operations='&')
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

Without any saved variables. The number of operations must equal the number of
categories minus one.

```python
wiki.get_set(['Countries in Asia',
              'Countries_in_Europe',
              'Russian-speaking_countries_and_territories'],
              operations=['or', 'and'])
# same as above
```

"""

from .mediawikitools import MediaWikiTools

from pkg_resources import get_distribution, DistributionNotFound
try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    pass  # package is not installed
