from typing import Tuple, Optional, List

from bibtexparser import Library
from bibtexparser.model import Entry, Field
from langcodes import Language
from lark import Tree
from dimcli import login, Dsl, DslDataset

from .base_connector import BaseConnector
from .connector_exceptions import ConnectorError, AuthorizationError, InvalidQueryError
from ..translators.dimensions_transformer import DimensionsTransformer
from .. import logger


class DimensionsConnector(BaseConnector):

    _MAX_BATCH_SIZE = 1000
    _DATABASE_NAME = "Dimensions"
    _ENDPOINT = "https://app.dimensions.ai/api/dsl/v2"

    def __init__(self,
                 _api_key: str):
        super().__init__()
        try:
            login(key=_api_key,
                  endpoint=self._ENDPOINT)
            self.dsl = Dsl()
        except Exception as e:
            raise AuthorizationError(f"Failed to initialize API client: {str(e)}")

    def search(self,
               query: Tree,
               start: int = 0,
               token: Optional[str] = None,
               language: Optional[Language] = None) -> Tuple[Library, int, Optional[str]]:
        """
        Executes a single-page search against the Dimensions database.

        :param query: The parsed query tree.
        :param start: The starting index for the results.
        :param token: Unused.
        :param language: Unused.
        :return: A tuple of (Library object with articles, total number of articles matching the query, None).
        :raises ConnectorError: For connector errors.
        """
        dsl_query = DimensionsTransformer().transform(query)
        if not dsl_query:
            raise InvalidQueryError("Empty query string.")

        # Add pagination to the query
        limit = self._MAX_BATCH_SIZE
        if start != 0:
            dsl_query += f" limit {limit} skip {start}"
        else:
            dsl_query += f" limit {limit}"
        try:
            logger.info(f"Executing query '{dsl_query}' on database '{self._DATABASE_NAME}' starting from {start}")

            response = self.dsl.query(dsl_query)
            if response:
                logger.debug(f"Retrieved data from {self._DATABASE_NAME}:\n {response.json}")

                return (self._parse_response(response),
                        response.count_total,
                        None)
        except Exception as e:
            raise ConnectorError(f"An error occurred: {str(e)}")

    def _parse_response(self, data: DslDataset) -> Library:
        library = Library()
        records = data['publications']  # List of publication records
        for rec in records:
            # Required

            # title
            title: str = rec.get("title", "")

            # pub_type, venue
            pub_type: str = ""
            venue: str = ""
            if rec.get("proceedings_title", ''):
                pub_type = "inproceedings"
                venue = rec.get("proceedings_title")
            elif rec.get("book_title", ''):
                pub_type = "inbook"
                venue = rec.get("book_title", '')
            elif rec.get("journal", {}):
                pub_type = "article"
                venue = rec.get('journal', {}).get('title', '')
            elif rec.get("book_series_title", ''):
                pub_type = "book"
                venue = rec.get('book_series_title', '')
            venue_key: str = self._PUB_TYPE_VENUE_MAP[pub_type]

            # year, month
            pub_date: str = str(rec.get('date', ''))
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
                pub_year = str(rec.get('year', ''))

            # author
            authors_list: List[dict] = rec.get("authors", [])
            authors: List[str] = [author.get("first_name", "") + " " + author.get("last_name", "") for author in authors_list]
            authors: str = ' and '.join([self._normalize_author_name(author.strip()) for author in authors])

            # doi
            doi: str = rec.get("doi", '')

            # url
            url: str = rec.get("linkout", '')

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
            if pub_month:
                entry.set_field(Field(key='month', value=pub_month))

            # Extras

            # volume
            volume: str = str(rec.get('volume', ''))
            if volume:
                entry.set_field(Field(key='volume', value=volume))

            # number
            issue: str = rec.get('issue', '')
            if issue:
                entry.set_field(Field(key='number', value=issue))

            # page
            pages: str = rec.get('pages', '')
            if pages:
                if '-' in pages and not '--' in pages:
                    pages = pages.replace(__old="-", __new="--")
                entry.set_field(Field(key='pages', value=pages))

            # abstract
            abstract = rec.get("abstract", None)
            if abstract:
                entry.set_field(Field(key='abstract', value=abstract))

            # keywords
            keywords = ", ".join(rec.get("concepts", []))
            if keywords:
                entry.set_field(Field(key='keywords', value=keywords))

            library.add(entry)

        return library
