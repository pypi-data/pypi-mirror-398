from typing import Tuple, Optional, List

from bibtexparser import Library
from bibtexparser.model import Entry, Field
from langcodes import Language
from lark import Tree

from .base_connector import BaseConnector
from .connector_exceptions import InvalidQueryError, ConnectorError, AuthorizationError
from .sdks.xploreapi import XPLORE
from ..translators.ieee_transformer import IEEETransformer
from .. import logger


class IEEEConnector(BaseConnector):

    _MAX_BATCH_SIZE = 200
    _DATABASE_NAME = "IEEE"
    _PUB_TYPE_MAP = {
        "Book": "inbook",
        "ebook": "inbook",
        "Conference": "inproceedings",
        "Early Access": "article",
        "Journal": "article",
        "Magazine": "misc",
        "Standard": "techreport",
        "Course": "misc"
    }

    def __init__(self,
                 _api_key: str):
        super().__init__()
        self.api = XPLORE(_api_key)

    def search(self,
               query: Tree,
               start: int = 0,
               token: Optional[str] = None,
               language: Optional[Language] = None) -> Tuple[Library, int, Optional[str]]:
        """
        Executes a search against the IEEE Xplore database.

        :param query: The parsed query tree.
        :param start: The starting index for the results.
        :param token: Unused.
        :param language: Unused.
        :return: A tuple of (Library object with articles, total number of articles matching the query, resumption_token).
        :raises ConnectorError: For connector errors.
        """
        query_string, start_year, end_year = IEEETransformer().transform(query)

        self.api.startingResult(start + 1)  # IEEE Xplore API uses 1-based indexing
        self.api.maximumResults(self.api.resultSetMaxCap)
        self.api.dataFormat('object')
        self.api.dataType('json')
        if query_string:
            self.api.queryText(query_string)
        else:
            raise InvalidQueryError("Empty query string.")
        if start_year:
            self.api.searchField('start_year', str(start_year))
        if end_year:
            self.api.searchField('end_year', str(end_year))
        try:
            logger.info(f"Executing query '{query_string}' on database '{self._DATABASE_NAME}' starting from {start}")

            response_data = self.api.callAPI()
            if 'error' in response_data:
                error_message = response_data.get('error')
                if 'Invalid API Key' in error_message:
                    raise AuthorizationError()
                else:
                    raise ConnectorError(f"An error occurred: {error_message}")
            else:
                return (self._parse_response(response_data),
                        int(response_data.get('total_records', 0)),
                        None)
        except Exception as e:
            raise ConnectorError(f"An error occurred: {str(e)}")



    def _parse_response(self,
                        data: dict) -> Library:
        library = Library()
        records = data.get('articles', [])
        for rec in records:
            # Required

            # pub_type
            pub_type: str = self._PUB_TYPE_MAP[rec.get('content_type', '')]
            venue_key: str = self._PUB_TYPE_VENUE_MAP[pub_type]

            # title
            title: str = rec.get('title', '')

            # venue
            venue: str = rec.get('publication_title', '')

            # author
            authors_list: List[dict] = rec.get('authors', [])
            author_list: List[str] = [author.get('full_name', '') for author in authors_list]
            authors: str = ' and '.join([self._normalize_author_name(author.strip()) for author in author_list])

            # doi
            doi: str = rec.get('doi', '')

            # year
            pub_year: str = rec.get('publication_year', '')

            # url
            url: str = rec.get('pdf_url', '')
            if not url:
                url = rec.get('html_url', '')  # Or 'pdf_url', but may require access
            if not url:
                url = rec.get('abstract_url', '')

            # publisher
            publisher: str = rec.get('publisher', '')

            # Create entry
            entry: Entry = Entry(entry_type=pub_type,
                                 key=self._create_entry_key(year=pub_year,
                                                            title=title,
                                                            doi=doi,
                                                            url=url),
                                 fields=[
                                     Field(key='author', value=authors),
                                     Field(key='year', value=pub_year),
                                     Field(key='title', value=title),
                                     Field(key=venue_key, value=venue),
                                     Field(key='publisher', value=publisher)
                                 ])
            if doi:
                entry.set_field(Field(key='doi', value=doi))
            if url:
                entry.set_field(Field(key='url', value=url))

            # Extras

            # abstract
            abstract: str = rec.get('abstract', '')
            if abstract:
                entry.set_field(Field(key='abstract', value=abstract))

            # address
            address: str = rec.get('conference_location', '')
            if address:
                entry.set_field(Field(key='address', value=address))

            # keywords
            keywords: List[str] = []
            index_terms: dict = rec.get('index_terms', {})
            if index_terms:
                for key in ['author_terms', 'ieee_terms']:
                    terms: List[str] = index_terms.get(key, [])
                    if terms:
                        if isinstance(terms, list):
                            keywords.extend(terms)
                        elif isinstance(terms, dict):
                            keywords.append(terms.get('term', ''))
            if keywords:
                entry.set_field(Field(key='keywords', value=', '.join(keyword.strip() for keyword in keywords)))

            #  volume
            volume: str = str(rec.get('volume', ''))
            if volume:
                entry.set_field(Field(key='volume', value=volume))

            # number
            issue: str = str(rec.get('issue', ''))
            if issue:
                entry.set_field(Field(key='number', value=issue))

            # page
            start_page: str = rec.get('start_page', '')
            end_page: str = rec.get('end_page', '')
            if start_page and end_page:
                entry.set_field(Field(key='pages', value=f'{start_page}--{end_page}'))

            library.add(entry)
        return library
