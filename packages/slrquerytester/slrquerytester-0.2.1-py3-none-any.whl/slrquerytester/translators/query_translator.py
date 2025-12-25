from typing import Tuple

from lark import Tree

from ..connectors.core_connector import COREConnector
from ..connectors.dimensions_connector import DimensionsConnector
from ..connectors.ieee_connector import  IEEEConnector
from ..connectors.lens_connector import  LENSConnector
from ..connectors.openalex_connector import OpenAlexConnector
from ..connectors.scopus_connector import ScopusConnectorFree, ScopusConnectorPremium
from ..connectors.springer_connector import SpringerConnectorFree, SpringerConnectorPremium
from ..connectors.wos_connector import WOSConnector
from .core_transformer import CORETransformer
from .dimensions_transformer import DimensionsTransformer
from .ieee_transformer import IEEETransformer
from .lens_transformer import LENSTransformer
from .openalex_transformer import OpenAlexTransformer
from .scopus_transformer import ScopusTransformer
from .springer_transformer import SpringerTransformerFree, SpringerTransformerPremium
from .wos_transformer import WOSTransformer


TRANSFORMER_MAP = {
    COREConnector.database_name(): CORETransformer,
    DimensionsConnector.database_name(): DimensionsTransformer,
    IEEEConnector.database_name(): IEEETransformer,
    LENSConnector.database_name(): LENSTransformer,
    OpenAlexConnector.database_name(): OpenAlexTransformer,
    ScopusConnectorFree.database_name(): ScopusTransformer,
    ScopusConnectorPremium.database_name(): ScopusTransformer,
    SpringerConnectorFree.database_name(): SpringerTransformerFree,
    SpringerConnectorPremium.database_name(): SpringerTransformerPremium,
    WOSConnector.database_name(): WOSTransformer
}


def translate_query(query: Tree, database_name: str) -> Tuple[str, int, int]:
    """
    Translates the query using the appropriate transformer based on the database name.

    :param query: The query tree to be transformed.
    :param database_name: The name of the database.
    :return: The transformed query as a string.
    :raises ValueError: If no transformer is found for the given database name.
    """
    transformer_class = TRANSFORMER_MAP.get(database_name)

    if not transformer_class:
        raise ValueError(f"No transformer found for database: {database_name}")

    transformer = transformer_class()
    return transformer.transform(query)
