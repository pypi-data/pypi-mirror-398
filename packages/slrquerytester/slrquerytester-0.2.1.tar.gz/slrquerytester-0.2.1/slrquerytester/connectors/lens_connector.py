from typing import Optional, Tuple, List

import requests
from bibtexparser import Library
from bibtexparser.model import Entry, Field
from langcodes import Language
from lark import Tree
from requests import Response

from .base_connector import BaseConnector
from .connector_exceptions import ConnectorError, InvalidQueryError
from ..translators.lens_transformer import LENSTransformer
from .. import logger


class LENSConnector(BaseConnector):

    _MAX_BATCH_SIZE = 1000
    _DATABASE_NAME = "LENS"
    _ENDPOINT = "https://api.lens.org/scholarly/search/"
    _PUB_TYPE_MAP = {
        "journal article": "article",
        "book": "book",
        "book chapter": "inbook",
        "conference proceedings article": 'inproceedings',
        "report": "techreport",
        "standard": "techreport",
        "dissertation": "phdthesis",
        "clinical study": "misc",
        "review": "article",
        "other": "misc",
        "unknown": "misc"
    }

    def __init__(self,
                 _api_key: str):
        super().__init__()
        self._HEADERS: dict = {
            'Authorization': f"Bearer {_api_key}",
            'Content-Type': 'application/json'
        }

    def search(self,
               query: Tree,
               start: int = 0,
               token: Optional[str] = None,
               language: Optional[Language] = None) -> Tuple[Library, int, Optional[str]]:
        """
        Executes a single-page search against the LENS database.

        :param query: The parsed query tree.
        :param start: The starting index for the results.
        :param token: The cursor value. If None, it means first call and we start with cursor='*'.
        :param language: langcodes.Language object. The language to filter results from if possible.
        :return: A tuple of (Library object with articles, total number of articles matching the query, resumption_token).
        :raises ConnectorError: For connector errors.
        """
        query_string = LENSTransformer().transform(tree=query)
        if not query_string:
            raise InvalidQueryError("Empty query string.")

        params: dict = {
            'query': query_string,
            'scroll': '1m',
            'size': self._MAX_BATCH_SIZE,
        }
        if token:
            params["scroll_id"] = token
        else:
            params['from'] = start + 1
        try:
            logger.info(f"Executing query '{query_string}' on database '{self._DATABASE_NAME}' starting from {start}")

            response: Response = requests.get(self._ENDPOINT,
                                              headers=self._HEADERS,
                                              params=params)
            if response.status_code == requests.codes.ok:
                data: dict = response.json()
                logger.debug(f"Retrieved data from {self._DATABASE_NAME}:\n {data}")

                return (self._parse_response(data=data, filter_language=language),
                        int(data.get('total', 0)),
                        str(data.get('scroll_id' '')))
            else:
                self._handle_http_error(response)
        except requests.exceptions.RequestException as e:
            raise ConnectorError(f"An error occurred: {str(e)}")

    def _parse_response(self,
                        data,
                        filter_language: Language = None) -> Library:
        library: Library = Library()
        records: List[dict] = data.get('data', [{}])
        for rec in records:
            if filter_language:
                languages = rec.get('languages', [])
                if not filter_language.language in [Language.get(language).language for language in languages]:
                    continue
            # Required

            # title
            title: str = rec.get('title', '')

            # pub_type
            pub_type: str = self._PUB_TYPE_MAP.get(rec.get('publication_type', ''), '')
            if not pub_type:
                continue
            venue_key: str = self._PUB_TYPE_VENUE_MAP[pub_type]

            # year, month
            pub_date: str = str(rec.get('date_published', ''))
            pub_year: str = ""
            pub_month: str = ""
            if pub_date:
                # e.g. "2024-08-13"
                try:
                    pub_year = str(int(pub_date.split("-")[0]))
                except (ValueError, IndexError):
                    pass
                try:
                    pub_month = str(int(pub_date.split("-")[1]))
                except (ValueError, IndexError):
                    pass
            else:
                pub_year = str(rec.get('year_published', ''))

            # author
            authors_list: List = rec.get('authors', [])
            author_list: List[str] = []
            for author in authors_list:
                lastname = author.get('last_name', '').strip()
                firstname = author.get('first_name', '').strip()
                initials = author.get('initials', '').strip()
                authname = author.get('collective_name', '').strip()
                # Construct a display name:
                # 1) If we have both surname and given-name, use "GivenName Surname".
                # 2) Else if we have surname + initials, use "Initials Surname".
                # 3) Else if authname is provided, use that as a fallback.
                # 4) Else if we only have surname or given-name, use whichever is available.
                # 5) If everything is absent, call them "Unknown Author".
                if lastname and firstname:
                    name = f"{firstname} {lastname}"
                elif lastname and initials:
                    name = f"{initials} {lastname}"
                elif authname:
                    name = authname
                elif lastname:
                    name = lastname
                elif firstname:
                    name = firstname
                else:
                    name = "Unknown Author"
                author_list.append(name)
            authors: str = ' and '.join([self._normalize_author_name(author.strip()) for author in author_list])

            # doi
            doi: str = ""
            external_ids : List = rec.get('external_ids', [])
            if external_ids:
                for external_id in external_ids:
                    if external_id.get("type", '') == "doi":
                        doi = external_id.get("value", '')

            # url
            url: str = ""
            pdf_url: str = ""
            html_url: str = ""
            source_urls = rec.get('source_urls', [])
            for source_url in source_urls:
                if source_url.get("type", '') == "pdf":
                    pdf_url = source_url.get('value', '')
                if source_url.get("type", '') == "html":
                    html_url = source_url.get('value', '')
            if pdf_url:
                url = pdf_url
            elif html_url:
                url = html_url
            elif doi:
                url = f'https://doi.org/{doi}'

            # venue, publisher, address
            venue: str = ''
            publisher: str = ''
            address: str = ''
            source = rec.get('source', {})
            if source:
                venue = source.get('title', '')
                publisher = source.get('publisher', '')
                conference = rec.get('conference', {})
                if venue_key == 'inproceedings' and conference:
                    address = conference.get('location', '')
                if not address:
                    address = source.get('country', '')

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
            if address:
                entry.set_field(Field(key='address', value=address))
            if pub_month:
                entry.set_field(Field(key='month', value=pub_month))

            # Extras

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

            # abstract
            abstract: str = rec.get('abstract', '')
            if abstract:
                entry.set_field(Field(key='abstract', value=abstract))

            # keywords
            keywords: List[str] = rec.get('keywords', [])
            if keywords:
                entry.set_field(Field(key='keywords', value=', '.join(keyword.strip() for keyword in keywords)))

            # add to library
            library.add(entry)
        return library