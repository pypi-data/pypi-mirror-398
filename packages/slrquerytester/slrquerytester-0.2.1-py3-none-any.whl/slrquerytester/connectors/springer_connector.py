from abc import ABCMeta
import requests
from typing import Optional, Tuple, List

from bibtexparser import Library
from bibtexparser.model import Entry, Field
from langcodes import Language
from lark import Tree
from requests import Response

from .base_connector import BaseConnector
from .connector_exceptions import ConnectorError, InvalidQueryError
from ..translators.springer_transformer import SpringerTransformerFree, SpringerTransformerPremium
from .. import logger


class SpringerConnector(BaseConnector, metaclass=ABCMeta):

    _BASE_URL = "https://api.springernature.com/meta/v2/json"
    _HEADERS = {
        "Accept": "application/json"
    }
    _TRANSFORMER = None
    _PUB_TYPE_MAP = {
        "Article": "article",
        "Chapter": "inbook",
        "Chapter ConferencePaper": "inproceedings",
        "Book": "book",
        "Chapter ReferenceWorkEntry": "inbook",
        "Chapter Protocol": "inbook"
    }

    def __init__(self,
                 _api_key: str):
        super().__init__()
        self._PARAMS = {
            "api_key": _api_key
        }

    def search(self,
               query: Tree,
               start: Optional[int] = 1,
               token: Optional[str] = None,
               language: Optional[Language] = None) -> Tuple[Library, int, Optional[str]]:
        """
        Executes a single-page search against the Springer Meta v2 API.

        :param query: The parsed query tree.
        :param start: The starting index for the results.
        :param token: Unused.
        :param language: langcodes.Language object. The language to filter results from if possible.
        :return: A tuple of (Library object with articles, total number of articles matching the query, None).
        :raises ConnectorError: For connector errors.
        """
        query_string = self._TRANSFORMER.transform(query)
        if not query_string:
            raise InvalidQueryError("Empty query string.")

        self._PARAMS.update({
            "q": query_string,
            "s": str(start),  # start index
            "p": str(self._MAX_BATCH_SIZE)  # page size
        })

        try:
            logger.info(f"Executing query '{query_string}' on database '{self._DATABASE_NAME}' starting from {start}")

            response : Response = requests.get(self._BASE_URL,
                                               headers=self._HEADERS,
                                               params=self._PARAMS)
            if response.status_code == requests.codes.ok:
                data: dict = response.json()
                logger.debug(f"Retrieved data from {self._DATABASE_NAME}:\n {data}")

                return (self._parse_response(data, language),
                        int(data.get("result", [])[0].get("total", "0")),
                        None)
            else:
                self._handle_http_error(response)
        except requests.exceptions.RequestException as e:
            raise ConnectorError(f"An error occurred: {str(e)}")

    def _parse_response(self,
                        data: dict,
                        filter_language=None) -> Library:
        library : Library = Library()
        records : List[dict] = data.get("records", [])
        for rec in records:
            if filter_language:
                language = rec.get('language', '')
                if language:
                    if filter_language.language != Language.get(language).language:
                        continue
            # Required

            # pub_type
            pub_type : str = self._PUB_TYPE_MAP[rec.get("contentType", "")]
            venue_key : str = self._PUB_TYPE_VENUE_MAP[pub_type]

            # title
            title : str = rec.get("title", "")

            # doi
            doi : str = rec.get("doi", "")

            # url
            url : str = ""
            url_entries : List = rec.get("url", [])
            if isinstance(url_entries, list) and len(url_entries) > 0:
                # Try to pick the pdf if available, else the first
                pdf_entry = next((u for u in url_entries if u.get("format") == "pdf"), None)
                if pdf_entry and pdf_entry.get("value"):
                    url = pdf_entry["value"]
                else:
                    # take the first with a "value"
                    for u in url_entries:
                        val = u.get("value")
                        if val:
                            url = val
                            break
            if (not url) and doi:
                url = f"https://doi.org/{doi}"

            # venue
            venue : str = rec.get("publicationName", "")

            # year, month
            pub_date : str = rec.get("publicationDate", "")
            pub_year : str = ""
            pub_month : str = ""
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

            # author
            author_list : List[str] = []
            if "creators" in rec:
                creator_list = rec["creators"]
                if isinstance(creator_list, list):
                    for creator in creator_list:
                        # creator might look like {"creator": "LastName, FirstName", "ORCID": "..."}
                        a_name = creator.get("creator", "Unknown Author")
                        author_list.append(a_name)
                else:
                    # single creator dict or string
                    if isinstance(creator_list, dict):
                        a_name = creator_list.get("creator", "Unknown Author")
                        author_list.append(a_name)
                    elif isinstance(creator_list, str):
                        author_list.append(creator_list)
            authors : str = ' and '.join([self._normalize_author_name(author.strip()) for author in author_list])

            # publisher
            publisher : str = rec.get('publisher', '')

            # Create entry
            entry = Entry(entry_type=pub_type,
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
            if pub_month:
                entry.set_field(Field(key='month', value=pub_month))

            # Extras

            # abstract
            abstract : str = rec.get("abstract", "")
            if abstract:
                entry.set_field(Field(key='abstract', value=abstract))

            # keywords
            keywords : List[str] = []
            if "keyword" in rec:
                kw_data = rec.get("keyword")
                if isinstance(kw_data, list):
                    keywords = [k.strip() for k in kw_data if k.strip()]
                elif isinstance(kw_data, str):
                    keywords = [k.strip() for k in kw_data.split(',')]
            if keywords:
                entry.set_field(Field(key='keywords', value=', '.join(keyword.strip() for keyword in keywords)))

            # volume
            volume : str = rec.get('volume', '')
            if volume:
                entry.set_field(Field(key='volume', value=volume))

            # issue
            issue : str = rec.get('number', '')
            if issue:
                entry.set_field(Field(key='number', value=issue))

            # page
            page_start : str = rec.get('startingPage', '')
            page_end : str = rec.get('endingPage', '')
            if page_start and page_end:
                entry.set_field(Field(key='page', value=f'{page_start}--{page_end}'))

            # add to library
            library.add(entry)
        return library

class SpringerConnectorFree(SpringerConnector):
    _MAX_BATCH_SIZE = 25
    _DATABASE_NAME = "Springer-Free"
    _TRANSFORMER = SpringerTransformerFree()

    def __init__(self, _api_key: str):
        super().__init__(_api_key)

class SpringerConnectorPremium(SpringerConnector):
    _MAX_BATCH_SIZE = 100
    _DATABASE_NAME = "Springer-Premium"
    _TRANSFORMER = SpringerTransformerPremium()

    def __init__(self, _api_key: str):
        super().__init__(_api_key)