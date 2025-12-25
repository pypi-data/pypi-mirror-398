from abc import ABC, abstractmethod
from typing import Tuple, Optional

from langcodes import Language
from bibtexparser import Library
from lark import Tree

from .connector_exceptions import InvalidQueryError, AuthorizationError, ConnectorError, RateLimitExceededError, ConnectorUnavailableError


class BaseConnector(ABC):
    """
    Abstract base class for all database connectors.
    """
    _MAX_BATCH_SIZE = None
    _DATABASE_NAME = None
    _PUB_TYPE_VENUE_MAP: dict = {
        'article': 'journal',
        'inproceedings': 'booktitle',
        'inbook': 'booktitle',
        'book': 'series',
        'phdthesis': 'school',
        'techreport': 'institution',
        'misc': 'booktitle'
    }

    @abstractmethod
    def search(self,
               query: Tree,
               start: int = 0,
               token: Optional[str] = None,
               language: Optional[Language] = None) -> Tuple[Library, int, Optional[str]]:
        """
        Executes a search against the database.

        :param query: The database-specific query string.
        :param start: The starting index for the results.
        :param token: Resumption token for fetching subsequent pages.
        :param language: langcodes.Language object. The language to filter results from if possible.
        :return: A tuple of (list of Article objects, total number of articles matching the query, resumption token).
        :raises ConnectorError: For general connector errors.
        """
        pass

    @classmethod
    def database_name(cls) -> str:
        """
        The name of the database.
        """
        return cls._DATABASE_NAME

    @classmethod
    def max_batch_size(cls) -> int:
        """
        The max_batch_size associated with the connector.
        """
        return cls._MAX_BATCH_SIZE

    @staticmethod
    def _handle_http_error(response):
        """
        Handle non-200 HTTP responses from a connector search call.
        """
        if response.status_code == 400:
            raise InvalidQueryError()
        elif response.status_code == 401:
            raise AuthorizationError()
        elif response.status_code == 404:
            raise ConnectorError("Resource not found.")
        elif response.status_code == 429:
            raise RateLimitExceededError()
        elif response.status_code == 500:
            raise ConnectorUnavailableError()
        else:
            raise ConnectorError(f"Unexpected error: {response.status_code} {response.text}")

    @staticmethod
    def _create_entry_key(year: str, title: str, doi: str, url: str):
        if doi:
            key = doi
        elif url:
            key = url
        else:
            key = f"{year}{title.replace(' ', '')[:max(19, len(title))]}"
        return key

    def _normalize_author_name(self, name: str) -> str:
        """
        Normalizes a BibTeX-style name into "First von Last, Jr" form if possible.
        If the name is fully braced (e.g., {Some, Inc.}), returns it as-is.
        """
        # If the entire name is enclosed in balanced outer braces, do NOT parse further.
        if self._is_fully_braced(name):
            return name

        # Count how many commas are in the name
        comma_count = name.count(',')

        if comma_count == 2:
            # Name format: "von Last, Jr, First"
            return self._from_von_last_jr_first(name)
        elif comma_count == 1:
            # Name format: "von Last, First"
            return self._from_von_last_first(name)
        else:
            # Name format: "First von Last" (no commas)
            return self._from_first_von_last(name)

    @staticmethod
    def _is_fully_braced(name: str) -> bool:
        """
        Check if a name is enclosed in balanced braces, e.g. '{Barnes and Noble, Inc.}'.
        A minimal approach:
          - name must start with '{' and end with '}'
          - attempt to verify braces are balanced within.
        """
        name = name.strip()
        if not (name.startswith('{') and name.endswith('}')):
            return False

        # Do a quick balanced-brace check:
        # Remove the first and last brace, then see if the remainder is balanced.
        inner = name[1:-1]
        brace_count = 0
        for char in inner:
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
            if brace_count < 0:
                # We closed more braces than opened
                return False

        # If we end up with brace_count=0, then it's properly balanced
        return brace_count == 0

    @staticmethod
    def _from_von_last_jr_first(name: str) -> str:
        """
        Parse "von Last, Jr, First" => "First von Last, Jr"
        """
        parts = [p.strip() for p in name.split(',')]
        # E.g., parts = [ 'von Last', 'Jr', 'First' ]
        von_last = parts[0]
        jr = parts[1]
        first = parts[2]

        # If needed, further parse von_last into separate 'von' + 'Last' pieces.
        # But for simplicity, we keep it as one chunk: "von Last".
        # We then reorder it to "First von Last, Jr".
        return f"{first} {von_last}, {jr}"

    @staticmethod
    def _from_von_last_first(name: str) -> str:
        """
        Parse "von Last, First" => "First von Last"
        """
        parts = [p.strip() for p in name.split(',')]
        # E.g., parts = [ 'von Last', 'First' ]
        von_last = parts[0]
        first = parts[1]

        return f"{first} {von_last}"

    @staticmethod
    def _from_first_von_last(name: str) -> str:
        """
        Handles a name with no commas, presumably "First von Last".
        However, we attempt to detect whether there is a 'von' part inside
        by analyzing the tokens from right to left.

        Minimal approach:
        1) Split on whitespace
        2) The rightmost token(s) are the last name
        3) Any continuous run of lowercased tokens (like 'de', 'van', etc.)
           to the LEFT of the last name get treated as 'von' part
        4) Everything else at the front is the first name
        """
        tokens = name.split()
        if not tokens:
            # Empty or bizarre input
            return name

        # We'll parse from the right to left to find where 'Last' begins.
        # Typically, 'Last' (surname) is the final token or tokens that are
        # capitalized or mixed. The 'von' part is typically purely lowercase.

        # Reverse tokens to iterate from last to first
        reversed_tokens = list(reversed(tokens))

        # Identify 'last' portion
        # We collect from the end to the first encountered lowercased token
        # that we interpret as 'von'. This is a naive approach, but fairly standard
        # for BibTeX parsing.

        last_parts = []
        von_parts = []
        first_parts = []

        # Start reading from the end:
        # - If the token is all-lowercase, we might call it von-part
        # - If the token has uppercase, we consider it part of the last name
        # We keep going until we see a purely-lowercase token to the left
        # of an uppercase token. Then everything else is 'first part'.

        # Example: "Jean de la Fontaine"
        # reversed => ["Fontaine", "la", "de", "Jean"]
        # => last = ["Fontaine"]
        # => von = ["la", "de"]
        # => first = ["Jean"]

        # We basically gather the last name until we find a fully-lower token that
        # appears to be 'von', but if we find multiple uppercase tokens, we consider them
        # all as part of the last name.
        # Then the remainder is 'first'.

        state = 'collect_last'
        for token in reversed_tokens:
            # Once we've assigned 'collect_von', if we see an uppercase token,
            # we revert to collecting in 'first'.
            if state == 'collect_last':
                if token.islower():
                    # This might be part of the von section,
                    # so move to collect_von
                    state = 'collect_von'
                    von_parts.append(token)
                else:
                    last_parts.append(token)
            elif state == 'collect_von':
                if token.islower():
                    von_parts.append(token)
                else:
                    # Now we consider anything left as part of 'first'
                    state = 'collect_first'
                    first_parts.append(token)
            else:
                # state == 'collect_first'
                first_parts.append(token)

        # Now we have reversed lists
        # Re-reverse them to get the correct order
        last_parts.reverse()
        von_parts.reverse()
        first_parts.reverse()

        # Join them
        # "First" is everything in first_parts
        # "von" is everything in von_parts
        # "Last" is everything in last_parts
        # e.g. "Jean" + "de la" + "Fontaine" => "Jean de la Fontaine"

        first_str = " ".join(first_parts)
        von_str = " ".join(von_parts)
        last_str = " ".join(last_parts)

        # Build final name
        if von_str and last_str:
            return f"{first_str} {von_str} {last_str}".strip()
        elif last_str:
            return f"{first_str} {last_str}".strip()
        else:
            # If for some reason there's no last_str, just return name as-is
            return name
