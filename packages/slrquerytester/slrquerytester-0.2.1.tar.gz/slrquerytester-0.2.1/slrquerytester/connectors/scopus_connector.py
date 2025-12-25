import re
from abc import ABCMeta
from typing import Optional, Tuple, List

import requests
from bibtexparser import Library
from bibtexparser.model import Entry, Field
from langcodes import Language
from lark import Tree
from requests import Response

from .base_connector import BaseConnector
from .connector_exceptions import ConnectorError, InvalidQueryError
from ..translators.scopus_transformer import ScopusTransformer
from .. import logger


class ScopusConnector(BaseConnector, metaclass=ABCMeta):

    _BASE_URL : str = 'https://api.elsevier.com/content/search/scopus'
    _PUB_TYPE_MAP : dict = {
        "Journal": "article",
        "Book": "inbook",
        "Conference Proceedings": "inproceedings",
        "Conference Proceeding": "inproceedings",
        "Book.Book": "book",
        "Book Series": "book",
        "Trade Journal": "article"
    }
    _VIEW = None

    def __init__(self,
                 _api_key: str):
        super().__init__()
        self._HEADERS : dict = {
            'X-ELS-APIKey': _api_key,
            'Accept': 'application/json'
        }

    def _parse_response(self,
                        data: dict) -> Library:
        library = Library()
        search_results = data.get('search-results', {})
        entries = search_results.get('entry', [])
        for entry in entries:
            # Required

            # pub_type
            agg_type = entry.get('prism:aggregationType')
            if agg_type == 'Book':
                if entry.get('subtypeDescription', '') == 'Book':
                    agg_type = 'Book.Book'
            pub_type : str = self._PUB_TYPE_MAP[agg_type]
            venue_key : str = self._PUB_TYPE_VENUE_MAP[pub_type]

            # title
            title = entry.get('dc:title', '')

            # author
            authors_list = []
            if 'author' in entry:
                # 'author' may be a list of dicts
                author_list = entry['author']
                if isinstance(author_list, dict):
                    # If it's just one author, wrap in a list
                    author_list = [author_list]
                for auth in author_list:
                    # Scopus can provide multiple name pieces:
                    #   surname      -> e.g. "Basso"
                    #   given-name   -> e.g. "Walter"
                    #   initials     -> e.g. "W."
                    #   authname     -> e.g. "Basso, W."
                    surname = auth.get('surname', '').strip()
                    given_name = auth.get('given-name', '').strip()
                    initials = auth.get('initials', '').strip()
                    authname = auth.get('authname', '').strip()
                    # Construct a display name:
                    # 1) If we have both surname and given-name, use "GivenName Surname".
                    # 2) Else if we have surname + initials, use "Initials Surname".
                    # 3) Else if authname is provided, use that as a fallback.
                    # 4) Else if we only have surname or given-name, use whichever is available.
                    # 5) If everything is absent, call them "Unknown Author".
                    if surname and given_name:
                        name = f"{given_name} {surname}"
                    elif surname and initials:
                        name = f"{initials} {surname}"
                    elif authname:
                        name = authname
                    elif surname:
                        name = surname
                    elif given_name:
                        name = given_name
                    else:
                        name = "Unknown Author"

                    authors_list.append(name)
            else:
                # Fallback to dc:creator if 'author' is not present
                creator = entry.get('dc:creator')
                if creator:
                    authors_list.append(creator)
            authors: str = ' and '.join([self._normalize_author_name(author.strip()) for author in authors_list])

            # doi
            doi = entry.get('prism:doi', None)

            # year, month
            cover_date : str = entry.get('prism:coverDate', '')
            pub_year : str = ''
            pub_month: str = ''
            if cover_date:
                try:
                    pub_year = str(int(cover_date.split("-")[0]))
                except (ValueError, IndexError):
                    pass
                try:
                    pub_month = str(int(cover_date.split("-")[1]))
                except (ValueError, IndexError):
                    pass

            # venue
            venue = entry.get('prism:publicationName', '')

            # url
            url: str = entry.get('prism:url', '')
            if (not url) and doi:
                url = f"https://doi.org/{doi}"

            # Create entry
            article = Entry(entry_type=pub_type,
                            key=self._create_entry_key(year=pub_year,
                                                       title=title,
                                                       doi=doi,
                                                       url=url),
                            fields=[
                                Field(key='author', value=authors),
                                Field(key='year', value=pub_year),
                                Field(key='title', value=title),
                                Field(key=venue_key, value=venue)
                          ])
            if doi:
                article.set_field(Field(key='doi', value=doi))
            if url:
                article.set_field(Field(key='url', value=url))
            if pub_month:
                article.set_field(Field(key='month', value=pub_month))

            # Extras

            # abstract
            abstract = entry.get('dc:description', '')
            if abstract:
                article.set_field(Field(key='abstract', value=abstract))

            # keywords
            keywords : List[str] = []
            authkeywords = entry.get('authkeywords')
            if authkeywords:
                if isinstance(authkeywords, str):
                    # Split by any of these delimiters: '|', ';', or ','
                    split_tokens = re.split(pattern=r'[|;,]+',
                                            string=authkeywords)
                    # Strip whitespace and ignore empty tokens
                    keywords = [k.strip() for k in split_tokens if k.strip()]
                elif isinstance(authkeywords, list):
                    for k in authkeywords:
                        if isinstance(k, str):
                            # You can similarly split each list item if it can also contain multiple delimiters
                            split_tokens = re.split(pattern=r'[|;,]+',
                                                    string=k)
                            keywords.extend([x.strip() for x in split_tokens if x.strip()])
            if keywords:
                article.set_field(Field(key='keywords', value=', '.join(keyword.strip() for keyword in keywords)))

            # volume
            volume : str = entry.get('prism:volume', '')
            if volume:
                article.set_field(Field(key='volume', value=volume))

            # issue
            issue : str = entry.get('prism:issueIdentifier', '')
            if issue:
                article.set_field(Field(key='number', value=issue))

            # page
            page: str = entry.get('prism:pageRange', '')
            if page:
                if page.find('-') and (not page.find('--')):
                    page = page.replace(__old='-', __new='--')
                article.set_field(Field(key='page', value=page))

            # add to library
            library.add(article)
        return library

class ScopusConnectorFree(ScopusConnector):

    _MAX_BATCH_SIZE = 25
    _DATABASE_NAME = "Scopus-Free"
    _VIEW = 'STANDARD'

    def __init__(self,
                 _api_key: str):
        super().__init__(_api_key)

    def search(self,
               query: Tree,
               start: Optional[int] = 0,
               token: Optional[str] = None,
               language: Optional[Language] = None) -> Tuple[Library, int, Optional[str]]:
        """
        Executes a single-page search against the Scopus Search API.

        :param query: The parsed query tree.
        :param start: The starting index for the results.
        :param token: Unused. The Scopus-Free quota does not support cursor-based pagination.
        :param language: Unused.
        :return: A tuple of (Library object with articles, total number of articles matching the query, None).
        :raises ConnectorError: For connector errors.
        """

        if not start < 5000:
            raise ConnectorError("The Scopus Free-quota does not support pagination greater than 5000 entries!")
        query_string = ScopusTransformer().transform(query)
        if not query_string:
            raise InvalidQueryError("Empty query string.")
        params : dict = {
            'query': query_string,
            'count': str(self._MAX_BATCH_SIZE),
            'view': self._VIEW,
            'start': str(start)
        }

        try:
            logger.info(f"Executing query '{query_string}' on database '{self._DATABASE_NAME}' starting from {start}")

            response : Response = requests.get(self._BASE_URL,
                                               headers=self._HEADERS,
                                               params=params)
            if response.status_code == 200:
                data: dict = response.json()
                logger.debug(f"Retrieved data from {self._DATABASE_NAME}:\n {data}")

                total_records : int = int(data.get('search-results', {}).get('opensearch:totalResults', 0))
                if total_records > 5000:
                    logger.warning("The total number of records is greater than what the Scopus Free-Quota allows you to obtain (i.e. 5000)")

                return (self._parse_response(data),
                        total_records,
                        None)
            else:
                self._handle_http_error(response)
        except requests.exceptions.RequestException as e:
            raise ConnectorError(f"An error occurred: {str(e)}")

class ScopusConnectorPremium(ScopusConnector):
    _MAX_BATCH_SIZE = 25
    _DATABASE_NAME = "Scopus-Premium"
    _VIEW = 'COMPLETE'

    def __init__(self,
                 _api_key: str):
        super().__init__(_api_key)

    def search(self,
               query: Tree,
               start: int = 0,
               token: Optional[str] = None,
               language: Optional[Language] = None) -> Tuple[Library, int, Optional[str]]:
        """
        Executes a single-page search against the Scopus Search API.

        :param query: The parsed query tree.
        :param start: The starting index for the results.
        :param token: The cursor value. If None, it means first call and we start with cursor='*'.
        :param language: Unused.
        :return: A tuple of (Library object with articles, total number of articles matching the query, resumption_token).
        :raises ConnectorError: For connector errors.
        """
        query_string = ScopusTransformer().transform(query)
        if not query_string:
            raise InvalidQueryError("Empty query string.")
        # If no token, start at the beginning: cursor = "*"
        # Else use the provided token as the cursor.
        params : dict = {
            'query': query_string,
            'count': str(self._MAX_BATCH_SIZE),
            'cursor': token if token else "*",
            'view': self._VIEW
        }
        if (not token) and start:
            params['start'] = str(start)

        try:
            logger.info(f"Executing query '{query_string}' on database '{self._DATABASE_NAME}' starting from {start}")

            response : Response = requests.get(self._BASE_URL,
                                               headers=self._HEADERS,
                                               params=params)
            if response.status_code == requests.codes.ok:
                data: dict = response.json()
                logger.debug(f"Retrieved data from {self._DATABASE_NAME}:\n {data}")

                next_cursor : str = ''
                cursor_info = data.get('search-results', {}).get('cursor', [])
                if isinstance(cursor_info, list) and len(cursor_info) > 0:
                    next_cursor = cursor_info[0].get('@next')

                return (self._parse_response(data),
                        int(data.get('search-results', {}).get('opensearch:totalResults', 0)),
                        next_cursor)
            else:
                self._handle_http_error(response)
        except requests.exceptions.RequestException as e:
            raise ConnectorError(f"An error occurred: {str(e)}")