from typing import Tuple, Optional, List
import requests
from bibtexparser import Library
from bibtexparser.model import Field, Entry
from langcodes import Language

from lark import Tree

from .base_connector import BaseConnector
from .connector_exceptions import InvalidQueryError, ConnectorError
from ..translators.core_transformer import CORETransformer
from .. import logger


class COREConnector(BaseConnector):

    _MAX_BATCH_SIZE = 100
    _DATABASE_NAME = "CORE"
    _ENDPOINT = "https://api.core.ac.uk/v3/search/works"
    _PUB_TYPE_MAP = {
        "presentation": "",
        "research": "article",
        "thesis": "phdthesis",
        '':''
    }

    def __init__(self, _api_key: str):
        super().__init__()
        self._HEADERS = {
            'Authorization': f'Bearer {_api_key}'
        }

    def search(self,
               query: Tree,
               start: int = 0,
               token: Optional[str] = None,
               language: Optional[Language] = None) -> Tuple[Library, int, Optional[str]]:
        """
        Executes a single-page search against the Dimensions database.

        :param query: The parsed query tree.
        :param start: The starting index for the results.
        :param token: The cursor value. If None, it means first call.
        :param language: langcodes.Language object. The language to filter results from if possible.
        :return: A tuple of (Library object with articles, total number of articles matching the query, resumption_token).
        :raises ConnectorError: For connector errors.
        """
        query_string = CORETransformer().transform(query)
        if not query_string:
            raise InvalidQueryError("Empty query string.")
        params = {
            'q': query_string + " AND documentType:\"research\"",
            'scroll': True,
            'offset': start,
            'limit': self.max_batch_size()
        }
        try:
            logger.info(f"Executing query '{query_string}' on database '{self._DATABASE_NAME}' starting from {start}")

            response = requests.get(url=self._ENDPOINT,
                                    headers=self._HEADERS,
                                    params=params)
            if response.status_code == requests.codes.ok:
                data: dict = response.json()
                logger.debug(f"Retrieved data from {self._DATABASE_NAME}:\n {data}")

                return (self._parse_response(data=data, filter_language=language),
                        data.get('total_hits', 0),
                        None)
            else:
                self._handle_http_error(response)
        except requests.exceptions.RequestException as e:
            raise ConnectorError(f"An error occurred: {str(e)}")

    def _parse_response(self,
                        data: dict,
                        filter_language: Language = None) -> Library:
        library = Library()
        records = data.get('results', [])
        for rec in records:
            if filter_language:
                language= rec.get('language')
                if language:
                    if isinstance(language, dict):
                        language = language.get('code', language.get('name', ''))
                    if Language.get(language).language != filter_language.language:
                        continue
            # Required

            # title
            title: str = rec.get('title', '')

            # pub_type
            pub_type: str = self._PUB_TYPE_MAP[rec.get('document_type', '')]
            if not pub_type:
                continue
            venue_key: str = self._PUB_TYPE_VENUE_MAP[pub_type]

            # author
            authors_list: List[str] = rec.get('authors', [])
            if not authors_list:
                continue
            authors: str = ' and '.join([self._normalize_author_name(author.strip()) for author in authors_list])

            # doi
            doi: str = rec.get('doi', '')
            if not doi:
                continue

            # year
            pub_year: str = rec.get('year_published', '')
            if not pub_year:
                continue
            # url
            url: str = rec.get('download_url', '')
            if not url:
                continue

            # publisher
            publisher: str = rec.get('publisher', '')
            if not publisher:
                continue

            # venue
            venue_list: List[dict] =rec.get('journals', [{}])
            if pub_type == 'article' and not venue_list:
                continue
            venue: str = venue_list[0].get('title', '')

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

            # keywords
            keywords_list = rec.get('subjects', [])
            keywords_list.extend(rec.get('tags', []))
            keywords = ", ".join(keywords_list)
            if keywords:
                entry.set_field(Field(key='keywords', value=keywords))

            library.add(entry)
        return library
