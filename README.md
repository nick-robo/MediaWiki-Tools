# MediaWiki Tools

[![Coverage Status](https://coveralls.io/repos/github/nick-robo/MediaWiki-Tools/badge.svg?branch=main)](https://coveralls.io/github/nick-robo/MediaWiki-Tools?branch=main)

A high level library containing set of tools for for filtering pages using the rich data available in MediaWikis such as categories and info boxes. Uses both web-scraping and API methods (where available and feasible) to gather information.

# Goals

- Generate useful data (and datasets) from a wiki.
- To work on any MediaWiki (including `fandom.com`) with or without api.
- Get arbitrary subsets of pages based on categories and template parameters (todo).
- Be very robust to variations and inconsistencies in user input.
- Be efficient.


# Installation

Install it using pip.

```
pip install mediawiki-tools
```

Requires python `>3.8` because I like the walrus operator.

# Usage

Check out the [basic usage](https://nick-robo.github.io/MediaWiki-Tools/mwtools.html) guide and detailed [API documentation](https://nick-robo.github.io/MediaWiki-Tools/mwtools/mediawikitools.html).

# Example

Question: Which countries in Asia use english as spoken Language?

Answer:
```python
from mwtools import MediaWikiTools

wiki = MediaWikiTools('en.wikipedia.org')

wiki.get_set(['Countries in Asia', 
              'English-speaking countries and territories'], 
             'and')
# ['Philippines', 'Pakistan', 'Bahrain', 'Singapore', 'Brunei', 'India']
```

Question: Which countries in Asia or Europe use english as spoken Language?

Answer:
```python
wiki.get_set(['Countries in Asia', 'Countries in Europe',
              'English-speaking countries and territories'], 
             ['or','and'])
# ['Philippines',
#  'United Kingdom',
#  'Brunei',
#  'Malta',
#  'India',
#  'Pakistan',
#  'Scotland',
#  'Republic of Ireland',
#  'Singapore',
#  'Bahrain']
```

Question: Which of these countries are not island nations?

Answer:
```python
wiki.get_set(['Countries in Asia', 'Countries in Europe',
              'English-speaking countries and territories',
              'Island countries'], 
             ['or', 'and', 'not'])
# ['Pakistan', 'India']
```

