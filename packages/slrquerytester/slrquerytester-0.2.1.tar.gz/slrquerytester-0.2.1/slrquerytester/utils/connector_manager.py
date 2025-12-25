import traceback
from typing import Optional
from uu import Error

import backoff
from langcodes import Language
from lark import Tree

from .. import logger
from .cache_manager import CacheManager
from ..connectors.base_connector import BaseConnector
from ..connectors.core_connector import COREConnector
from ..connectors.dimensions_connector import DimensionsConnector
from ..connectors.ieee_connector import IEEEConnector
from ..connectors.lens_connector import LENSConnector
from ..connectors.openalex_connector import OpenAlexConnector
from ..connectors.scopus_connector import ScopusConnectorFree, ScopusConnectorPremium
from ..connectors.springer_connector import SpringerConnectorFree, SpringerConnectorPremium
from ..connectors.wos_connector import WOSConnector
from ..connectors.connector_exceptions import (AuthorizationError,
                                               InvalidQueryError,
                                               ConnectorError,
                                               RateLimitExceededError,
                                               ConnectorUnavailableError)


class ConnectorManager:

    def __init__(self,
                 _api_keys: dict):
        self.connectors = []
        self._prepare_connectors(_api_keys)
        if not self.connectors:
            logger.error("No database connectors configured. Please provide API keys in the configuration file.")
            raise ValueError("No database connectors configured. Please provide API keys in the configuration file.")

    def _prepare_connectors(self,
                            _api_keys: dict):
        """
        Prepare database connectors based on available API keys.

        :param _api_keys: Dictionary of API keys from the config.
        :return: List of initialized connector objects.
        """

        if COREConnector.database_name() in _api_keys:
            self.connectors.append(COREConnector(_api_key=_api_keys[COREConnector.database_name()]))

        if DimensionsConnector.database_name() in _api_keys:
            self.connectors.append(DimensionsConnector(_api_key=_api_keys[DimensionsConnector.database_name()]))

        if IEEEConnector.database_name() in _api_keys:
            self.connectors.append(IEEEConnector(_api_key=_api_keys[IEEEConnector.database_name()]))

        if LENSConnector.database_name() in _api_keys:
            self.connectors.append(LENSConnector(_api_key=_api_keys[LENSConnector.database_name()]))

        if OpenAlexConnector.database_name() in _api_keys:
            self.connectors.append(OpenAlexConnector(_api_key=_api_keys[OpenAlexConnector.database_name()]))

        if ScopusConnectorFree.database_name() in _api_keys:
            self.connectors.append(ScopusConnectorFree(_api_key=_api_keys[ScopusConnectorFree.database_name()]))

        if ScopusConnectorPremium.database_name() in _api_keys:
            self.connectors.append(ScopusConnectorPremium(_api_key=_api_keys[ScopusConnectorPremium.database_name()]))

        if SpringerConnectorFree.database_name() in _api_keys:
            self.connectors.append(SpringerConnectorFree(_api_key=_api_keys[SpringerConnectorFree.database_name()]))

        if SpringerConnectorPremium.database_name() in _api_keys:
            self.connectors.append(SpringerConnectorPremium(_api_key=_api_keys[SpringerConnectorPremium.database_name()]))

        if WOSConnector.database_name() in _api_keys:
            self.connectors.append(WOSConnector(_api_key=_api_keys[WOSConnector.database_name()]))

    @staticmethod
    def execute_and_cache_query(connector: BaseConnector,
                                query: Tree,
                                query_string: str,
                                cache_manager: CacheManager,
                                start: int = 0,
                                clear_cache: bool = False,
                                language: Optional[Language] = None):
        """
        Execute a query on the given connector and cache the retrieved results.

        This method fetches batches of articles using the connector's `search` method and caches them incrementally.
        It also handles error cases, retrying operations on certain failures using an exponential backoff strategy.

        :param connector: The connector used to execute the query.
        :param query: The parsed query tree to execute.
        :param query_string: The string representation of the query.
        :param cache_manager: The CacheManager responsible for caching the retrieved articles.
        :param start: The starting index for the query (default is 0).
        :param clear_cache: Whether to clear existing cached results for the query before executing (default is False).
        :param language: Optional language specification for the query.
        """
        database_name = connector.database_name()
        logger.info(f"Executing query '{query_string}' on database '{database_name}' starting from {start}")

        if clear_cache:
            cache_manager.clear_result_cache(query_string, database_name)

        total_results = None
        current_start = start
        resumption_token = None

        # Define a backoff strategy with exponential backoff
        def giveup(e):
            return isinstance(e, (AuthorizationError, InvalidQueryError))

        @backoff.on_exception(
            backoff.expo,
            (RateLimitExceededError, ConnectorUnavailableError, ConnectorError),
            max_tries=5,
            factor=2,
            jitter=backoff.full_jitter,
            giveup=giveup,
            on_backoff=ConnectorManager._log_backoff
        )
        def fetch_batch():
            return connector.search(
                query=query,
                start=current_start,
                token=resumption_token,
                language=language
            )

        while True:
            try:
                library, total, resumption_token = fetch_batch()

                if total_results is None:
                    total_results = total
                    cache_manager.set_expected_num_articles(query_string, database_name, total_results)

                if not library:
                    logger.info(f"No more articles found for query '{query_string}' in database '{database_name}'.")
                    break

                # Cache the retrieved articles
                cache_manager.cache_api_articles(library, query, database_name, total_results)
                current_start += len(library.entries)
                cache_manager.set_num_articles_retrieved(query_string, database_name, current_start)

                logger.info(f"Retrieved {len(library.entries)} articles from '{database_name}'. Total retrieved: {current_start}/{total_results}")

                if current_start >= total_results:
                    logger.info(f"All articles retrieved for query '{query_string}' from '{database_name}'.")
                    break

            except AuthorizationError:
                logger.error(f"Authorization failed for '{database_name}': {traceback.format_exc()}")
                break

            except InvalidQueryError:
                logger.error(f"Invalid query for '{database_name}': {traceback.format_exc()}")
                break

            except ConnectorError:
                logger.error(f"An error occurred with connector '{database_name}': {traceback.format_exc()}")
                break

            except Error:
                logger.error(f"An unexpected error occurred with connector '{database_name}': {traceback.format_exc()}")
                break

        logger.info(f"Finished executing query '{query_string}' on database '{database_name}'. Total articles retrieved: {current_start}")

    @staticmethod
    def _log_backoff(details):
        """
        Log backoff events.

        :param details: Details about the backoff event.
        """
        logger.warning(
            f"Backing off {details['wait']:0.1f} seconds after {details['tries']} tries "
            f"calling function {details['target'].__name__} with args {details['args']} and kwargs {details['kwargs']}"
        )