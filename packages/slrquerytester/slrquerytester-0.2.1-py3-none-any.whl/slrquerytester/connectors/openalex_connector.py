import requests
from typing import Optional, Tuple, List

from bibtexparser import Library
from bibtexparser.model import Entry, Field
from langcodes import Language
from lark import Tree

from .base_connector import BaseConnector
from .connector_exceptions import ConnectorError, InvalidQueryError
from ..translators.openalex_transformer import OpenAlexTransformer
from .. import logger


class OpenAlexConnector(BaseConnector):

    _MAX_BATCH_SIZE = 200
    _DATABASE_NAME = "OpenAlex"
    _BASE_URL : str = 'https://api.openalex.org/works'
    _PUB_TYPE_MAP : dict = {
        "article": "article",
        "book-chapter": "inbook",
        "dataset": "misc",
        "preprint": "article",
        "dissertation": "phdthesis",
        "book": "book",
        "review": "article",
        "other": "",
        "report": "techreport",
        "standard": "techreport",
        "reference-entry": '',
        'letter': '',
        'erratum': '',
        'editorial': ''
    }
    _SOURCE_TYPE_MAP : dict = {
        "repository" : "article",
        "journal" : "article",
        "conference" : "inproceedings",
        "book series" : "book",
        "ebook" : "inbook",
        "platform" : "article",
        "metadata" : "misc",
        "other" : "misc"
    }
    _PAGE_LIMIT : int = 10000

    def __init__(self,
                 _api_key: str):
        super().__init__()
        self._PARAMS = {"mailto": _api_key}

    def search(self,
               query: Tree,
               start: int = 0,
               token: Optional[str] = None,
               language: Optional[Language] = None) -> Tuple[Library, int, Optional[str]]:
        """
        Execute a search against the OpenAlex Works API.

        :param query: The parsed query tree.
        :param start: The starting index for the results.
        :param token: The cursor value. If None, it means first call.
        :param language: langcodes.Language object. The language to filter results from if possible.
        :return: A tuple of (Library object with articles, total number of articles matching the query, resumption_token).
        :raises ConnectorError: For connector errors.
        """
        query_string = OpenAlexTransformer().transform(query)
        if not query_string:
            raise InvalidQueryError("Empty query string.")
        self._PARAMS.update({
            'filter': query_string,
            'per-page': self._MAX_BATCH_SIZE,
            'select': 'display_name,abstract_inverted_index,doi,publication_year,authorships,primary_location,keywords,id,is_paratext,is_retracted,type,publication_date,id,biblio'
        })

        if (not token) and start:
            if start > self._PAGE_LIMIT:
                self._PARAMS['page'] = int(self._PAGE_LIMIT / self._MAX_BATCH_SIZE)
            else:
                self._PARAMS['page'] = str(int(start / self._MAX_BATCH_SIZE) + 1)

        try:
            logger.info(f"Executing query '{query_string}' on database '{self._DATABASE_NAME}' starting from {start}")

            response = requests.get(self._BASE_URL,
                                    params=self._PARAMS)
            if response.status_code == requests.codes.ok:
                data: dict = response.json()
                logger.debug(f"Retrieved data from {self._DATABASE_NAME}:\n {data}")

                return (self._parse_response(data=data, filter_language=language),
                        data.get('meta', {}).get('count', 0),
                        data.get('meta', {}).get('next_cursor', None))
            else:
                self._handle_http_error(response)
        except requests.exceptions.RequestException as e:
            raise ConnectorError(f"An error occurred: {str(e)}")

    def _parse_response(self,
                        data: dict,
                        filter_language: Language = None) -> Library:
        library = Library()
        results : List[dict] = data.get('results', [])
        for item in results:
            if item.get('is_paratext', False) or item.get('is_retracted', False):
                continue
            if filter_language:
                language = item.get('language', '')
                if language:
                    if filter_language.language != Language.get(language).language:
                        continue
            # Required

            # venue
            venue = ''
            primary_loc = item.get('primary_location', {})
            if not primary_loc:
                continue
            source = primary_loc.get('source', {})
            if source:
                venue = source.get('display_name', '')
            else:
                continue

            # pub_type
            item_type = item.get('type', '')
            if item_type:
                if not self._PUB_TYPE_MAP[item_type]:
                    continue
                if item_type == 'article' and source.get('type', '') == 'conference':
                    pub_type = 'inproceedings'
            else:
                item_type = self._SOURCE_TYPE_MAP[source.get('type', '')]
            pub_type = ''
            if item_type:
                pub_type = self._PUB_TYPE_MAP[item_type]
            else:
                pub_type = 'misc'

            venue_key: str = self._PUB_TYPE_VENUE_MAP[pub_type]

            # title
            title : str = item.get('display_name', '')

            # year, month
            cover_date : str = item.get('publication_date', '')
            pub_year: str = ''
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
            if not pub_year:
                pub_year = item.get('publication_year', '')

            # doi
            doi : str = item.get('doi', '')
            if doi:
                doi = doi.strip().removeprefix('https://doi.org/')
            else:
                continue

            # url
            url : str = item.get('id')

            # author
            author_list : List[str] = []
            authorships = item.get('authorships', [])
            for auth in authorships:
                author_obj = auth.get('author', {})
                author_name = author_obj.get('display_name')
                if author_name:
                    author_list.append(author_name)
            authors: str = ' and '.join([self._normalize_author_name(author.strip()) for author in author_list])

            # Create entry
            entry = Entry(entry_type=pub_type,
                            key=self._create_entry_key(year=pub_year,
                                                       title=title,
                                                       doi=doi,
                                                       url=url),
                            fields=[
                                Field(key='author', value=authors),
                                Field(key='year', value=pub_year),
                                Field(key='title', value=title)
                            ])
            if venue:
                entry.set_field(Field(key=venue_key, value=venue))
            if doi:
                entry.set_field(Field(key='doi', value=doi))
            if url:
                entry.set_field(Field(key='url', value=url))
            if pub_month:
                entry.set_field(Field(key='month', value=pub_month))

            # Extras

            # publisher
            publisher = source.get("host_organization_name")
            if publisher:
                entry.set_field(Field(key='publisher', value=publisher))

            # keywords
            keywords = []
            concepts = item.get('keywords', [])
            for c in concepts:
                kw = c.get('display_name')
                if kw:
                    keywords.append(kw)
            if keywords:
                entry.set_field(Field(key='keywords', value=', '.join(keyword.strip() for keyword in keywords)))

            # abstract
            abstract = self._reconstruct_abstract(item.get('abstract_inverted_index', {}))
            if abstract:
                entry.set_field(Field(key='abstract', value=abstract))

            # volume
            biblio_data : dict = item.get('biblio', {})
            volume : str = biblio_data.get('volume', '')
            if volume:
                entry.set_field(Field(key='volume', value=volume))

            # issue
            issue : str = biblio_data.get('issue', '')
            if issue:
                entry.set_field(Field(key='number', value=issue))

            # page
            page_start = biblio_data.get('first_page', '')
            page_end = biblio_data.get('last_page', '')
            if page_start and page_end:
                entry.set_field(Field(key='page', value=f'{page_start}--{page_end}'))

            # add to library
            library.add(entry)
        return library

    @staticmethod
    def _reconstruct_abstract(abstract_inverted_index: dict) -> Optional[str]:
        """
        Reconstruct the abstract text from the abstract_inverted_index.

        :param abstract_inverted_index: A dict where keys are words and values are lists of positions where the word appears.
        :return: A reconstructed abstract as a string, or None if not available.
        """
        if not abstract_inverted_index:
            return None

        # Create a position->word mapping
        pos_to_word = {}
        for word, positions in abstract_inverted_index.items():
            for pos in positions:
                pos_to_word[pos] = word

        # Sort by position and join
        sorted_positions = sorted(pos_to_word.keys())
        reconstructed = ' '.join(pos_to_word[p] for p in sorted_positions)
        return reconstructed

