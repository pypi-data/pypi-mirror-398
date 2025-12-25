from datetime import datetime
from typing import Optional, Tuple, List

import requests
from bibtexparser import Library
from bibtexparser.model import Entry, Field
from langcodes import Language
from lark import Tree
from requests import Response

from .base_connector import BaseConnector
from .connector_exceptions import ConnectorError, InvalidQueryError
from ..translators.wos_transformer import WOSTransformer
from .. import logger


class WOSConnector(BaseConnector):

    _MAX_BATCH_SIZE = 100
    _DATABASE_NAME = "WOS"
    _ENDPOINT: str = 'https://wos-api.clarivate.com/api/wos/'
    _PUB_TYPE_MAP: dict = {
        'Journal':'article',
        'Book':'book',
        'Series':'inproceedings',
        'Chapter':'inbook',
        'Books in series':'book',
        'Book in series': 'book'
    }
    _MONTH_LIST: List[str] = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']

    def __init__(self,
                 _api_key: str):
        super().__init__()
        self._HEADERS : dict = {
            'X-ApiKey': _api_key
        }

    def search(self,
               query: Tree,
               start: int = 0,
               token: Optional[str] = None,
               language: Optional[Language] = None) -> Tuple[Library, int, Optional[str]]:
        """
        Executes a single-page search against the Web of Science database.

        :param query: The parsed query tree.
        :param start: The starting index for the results.
        :param token: Unused.
        :param language: langcodes.Language object. The language to filter results from if possible.
        :return: A tuple of (Library, total number of articles matching the query, None).
        :raises ConnectorError: For connector errors.
        """
        query_string, start_year, stop_year = WOSTransformer().transform(tree=query)
        if not query_string:
            raise InvalidQueryError("Empty query string.")
        params : dict = {
            'databaseId': 'WOS',  # Search only in the Web of Science Core Collection
            'usrQuery': query_string,
            'count': self._MAX_BATCH_SIZE,
            'firstRecord': start + 1  # WOS API uses 1-based indexing
        }
        if start_year and stop_year:
            params['publishTimeSpan'] = f"{str(start_year)}-01-01+{str(stop_year)}-12-31"
        elif start_year:
            params['publishTimeSpan'] = f"{str(start_year)}-01-01+{str(datetime.now().year)}-12-31"
        elif stop_year:
            params['publishTimeSpan'] = f"1900-01-01+{str(stop_year)}-12-31" #WOS indexes articles upto 1900 CE
        try:
            logger.info(f"Executing query '{query_string}' with publishTimeSpan={params['publishTimeSpan']} on database '{self._DATABASE_NAME}' starting from {start}")

            response: Response = requests.get(self._ENDPOINT,
                                              headers=self._HEADERS,
                                              params=params)
            if response.status_code == requests.codes.ok:
                data: dict = response.json()
                logger.debug(f"Retrieved data from {self._DATABASE_NAME}:\n {data}")

                return (self._parse_response(data=data, filter_language=language),
                        int(data.get('QueryResult', {}).get('RecordsFound', 0)),
                        None)
            else:
                self._handle_http_error(response)
        except requests.exceptions.RequestException as e:
            raise ConnectorError(f"An error occurred: {str(e)}")

    def _parse_response(self,
                        data: dict,
                        filter_language: Language = None) -> Library:
        library : Library = Library()
        records : List[dict] = data.get('Data', {}).get('Records', {}).get('records', {}).get('REC', [])
        for rec in records:
            static_data : dict = rec.get('static_data', {})
            summary : dict = static_data.get('summary', {})
            fullrecord_metadata: dict = static_data.get('fullrecord_metadata', {})
            if filter_language:
                language = None
                languages: List = fullrecord_metadata.get('normalized_languages', fullrecord_metadata.get('languages', []))
                if languages:
                    for lang in languages:
                        if lang.get('type') == 'primary':
                            lang_content = lang.get('content', '')
                            language = Language.get(lang_content) if lang_content else None
                    if language:
                        if language.language != filter_language.language:
                            continue
            # Required

            # title, venue
            titles = summary.get('titles', {})
            title = ''
            venue = ''
            if 'title' in titles:
                title_list = titles['title']
                if isinstance(title_list, dict):
                    title_list = [title_list]
                for t in title_list:
                    if t.get('type') == 'item':
                        title = t.get('content', '')
                    elif t.get('type') == 'source':
                        venue = t.get('content', '')


            # pub_type
            pub_info : dict = summary.get('pub_info', {})
            pub_type : str = self._PUB_TYPE_MAP[pub_info.get('pubtype', '')]
            venue_key : str = self._PUB_TYPE_VENUE_MAP[pub_type]

            # year
            pub_year : str = str(pub_info.get('pubyear', ''))

            # author
            names : dict = summary.get('names', {})
            author_list : List[str] = []
            if 'name' in names:
                name_list = names['name']
                if isinstance(name_list, dict):
                    name_list = [name_list]
                for name in name_list:
                    display_name = name.get('display_name')
                    if display_name:
                        author_list.append(display_name)
            authors : str = ' and '.join([self._normalize_author_name(author.strip()) for author in author_list])

            # doi
            doi : str = ""
            identifiers = rec.get('dynamic_data', {}).get('cluster_related', {}).get('identifiers', {})
            if 'identifier' in identifiers:
                identifier_list = identifiers['identifier']
                if isinstance(identifier_list, dict):
                    identifier_list = [identifier_list]
                for identifier in identifier_list:
                    if identifier.get('type') == 'doi':
                        doi = identifier.get('value')
                        break

            # url
            if doi:
                url : str = f'https://doi.org/{doi}'
            else:
                # Fallback to UID URL if DOI is not available
                uid = rec.get('UID')
                if uid:
                    url = f'https://www.webofscience.com/wos/woscc/full-record/{uid}'
                else:
                    url = ""

            # publisher and address
            publisher : str = ''
            address : str = ''
            if 'publishers' in summary:
                publishers = summary.get('publishers', {})
                if 'publisher' in publishers:
                    publisher_info = publishers.get('publisher', {})
                    if 'names' in publisher_info:
                        publisher_names = publisher_info.get('names', {})
                        if 'name' in publisher_names:
                            publisher_name = publisher_names.get('name', {})
                            if 'full_name' in publisher_name:
                                publisher = publisher_name.get('full_name', '')
                            elif 'display_name' in publisher_name:
                                publisher = publisher_name.get('full_name', '')
                            else:
                                publisher = publisher_name.get('unified_name', '')
                    if 'address_spec' in publisher_info:
                        publisher_address: dict = publisher_info.get('address_spec', {})
                        if 'full_address' in publisher_address:
                            address = publisher_address.get('full_address', '')
                        else:
                            address = publisher_address.get('city', '')

            # Create entry
            entry : Entry = Entry(entry_type=pub_type,
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
            if address:
                entry.set_field(Field(key='address', value=address))

            # Extras

            #  volume
            volume : str = str(pub_info.get('vol', ''))
            if volume:
                entry.set_field(Field(key='volume', value=volume))

            # number
            issue : str = str(pub_info.get('issue', ''))
            if issue:
                entry.set_field(Field(key='number', value=issue))

            # month
            pub_month : str = pub_info.get('pubmonth', '')
            if pub_month:
                if len(pub_month) > 3:
                    for month in self._MONTH_LIST:
                        if month in pub_month:
                            pub_month = month
                pub_month = str(self._MONTH_LIST.index(pub_month) + 1)
                entry.set_field(Field(key='month', value=pub_month))

            # page
            page : str = ''
            if 'page' in pub_info:
                page_info : dict = pub_info.get('page', {})
                if 'content' in page_info:
                    page = page_info.get('content')
                    if '-' in page and (not '--' in page):
                        page = page.replace(__old='-', __new='--')
                else:
                    page = f"{page_info.get('begin')}--{page_info.get('end')}"
            if not "None" in page:
                entry.set_field(Field(key='pages', value=page))

            # abstract
            abstract : str = ''
            abstracts = fullrecord_metadata.get('abstracts', {})
            if 'abstract' in abstracts:
                abstract_content = abstracts['abstract']
                if isinstance(abstract_content, dict):
                    abstract_text = abstract_content.get('abstract_text', {})
                    p = abstract_text.get('p')
                    if isinstance(p, list):
                        abstract = ' '.join(p)
                    elif isinstance(p, str):
                        abstract = p
            if abstract:
                entry.set_field(Field(key='abstract', value=abstract))

            # keywords
            keywords : List[str] = []
            if 'keywords' in fullrecord_metadata:
                keywords_section = fullrecord_metadata['keywords']
                if 'keyword' in keywords_section:
                    keyword_list = keywords_section['keyword']
                    if isinstance(keyword_list, str):
                        keywords.append(keyword_list)
                    elif isinstance(keyword_list, list):
                        keywords.extend(keyword_list)
            if keywords:
                entry.set_field(Field(key='keywords', value=', '.join(keyword.strip() for keyword in keywords)))

            # add to library
            library.add(entry)
        return library