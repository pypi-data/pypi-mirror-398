import logging
from typing import List, Dict, Optional

from langcodes import Language
from lark import Tree

from .cache_manager import CacheManager
from .connector_manager import ConnectorManager
from ..translators.base_transformer import BaseTransformer
from .query_parser import parse_with_semantic_check
from .. import logger

class QueryProcessor:
    """
    Handles the processing of search queries by parsing, decomposing, and delegating query execution.
    """

    @staticmethod
    def process_queries(queries_json: List[Dict],
                        connector_manager: ConnectorManager,
                        cache_manager: CacheManager,
                        language: Optional[Language] = None):
        """
        Process each query (if the cache is stale, nonexistent, or incomplete) using the ConnectorManager object.

        :param queries_json: List of queries.
        :param connector_manager: ConnectorManager object.
        :param cache_manager: CacheManager object.
        :param language: langcodes.Language object. The language to filter results from if possible.
        """
        for query_json_entry in queries_json:
            query_string = query_json_entry['query']
            decomposition_level = query_json_entry['decomposition_level']
            logger.info(f"Processing query: {query_string}")
            parse_tree = parse_with_semantic_check(query_string)
            subqueries = QueryProcessor._decompose_query(parse_tree, max_depth=decomposition_level)

            if subqueries:
                for subquery in subqueries:
                    QueryProcessor._process_query(subquery, connector_manager, cache_manager, language)
            else:
                QueryProcessor._process_query(parse_tree, connector_manager, cache_manager, language)

    @staticmethod
    def _process_query(query: Tree,
                       connector_manager: ConnectorManager,
                       cache_manager: CacheManager,
                       language: Optional[Language] = None):
        """
        Process an individual query by checking its cache status and executing if needed.

        Depending on whether the query is found in the cache, is stale, or partially complete,
        this function decides if the query should be executed or retrieved directly from the cache.

        :param query: Parsed query tree.
        :param connector_manager: Manager for database connectors.
        :param cache_manager: CacheManager object.
        :param language: Optional language filter.
        """
        for connector in connector_manager.connectors:
            database_name = connector.database_name()
            base_transformer = BaseTransformer()
            query_string = base_transformer.transform(query)
            logger.debug(f"Processing query {query_string} for database: {database_name}")
            if not cache_manager.is_result_present(query_string, database_name):
                logger.debug(f"Query '{query_string}' for database '{database_name}' does not exist in cache.")
                connector_manager.execute_and_cache_query(connector, query, query_string, cache_manager, start=0, language=language)
            elif cache_manager.is_result_stale(query_string, database_name):
                logger.debug(f"Result of query '{query_string}' for database '{database_name}' is stale.")
                connector_manager.execute_and_cache_query(connector, query, query_string, cache_manager, start=0, clear_cache=True, language=language)
            elif cache_manager.is_result_partial(query_string, database_name):
                logger.debug(f"Result of query '{query_string}' for database '{database_name}' is incomplete.")
                num_retrieved = cache_manager.get_num_articles_retrieved(query_string, database_name)
                connector_manager.execute_and_cache_query(connector, query, query_string, cache_manager, start=num_retrieved, language=language)
            else:
                logger.debug(f"Result of query '{query_string}' for database '{database_name}' is up to date.")

    @staticmethod
    def _decompose_query(node: Tree,
                         max_depth: int,
                         current_depth: int = 0):
        """
        Decompose the query into valid subqueries

        This decomposition logic ensures:
         - A standalone date_expr is not considered a valid subquery.
         - A valid subquery must contain at least one normal_term.
         - "AND NOT" cannot appear alone, because the grammar already disallows standalone NOT.

        :param node: Root parse tree node (lark.Tree).
        :param max_depth: Maximum depth of recursion for decomposition.
        :param current_depth: The current recursion depth.
        :return: A list of subquery parse tree nodes that are valid and can be executed independently.
        """

        # If node is just a single date expression, it's invalid as a subquery
        if QueryProcessor._is_single_date_expr(node):
            return []

        # If max_depth is reached and node does not contain a date_expr, stop further decomposition
        # Return [node] if it's valid, else []
        if current_depth >= max_depth and not QueryProcessor._contains_date_expr(node):
            if QueryProcessor._is_valid_subquery(node):
                return [node]
            else:
                return []

        # Check for top-level or/and expressions where we can decompose further
        if isinstance(node, Tree) and node.data in ("or_expr", "and_expr"):
            # We'll look at children and attempt to separate date expressions from normal terms
            date_exprs = []
            other_terms = []

            # Partition children into date_exprs vs. non-date
            for child in node.children:
                if QueryProcessor._is_date_expr(child):
                    date_exprs.append(child)
                else:
                    other_terms.append(child)

            subqueries = []

            if date_exprs:
                # If there are date expressions mixed in
                if other_terms:
                    # Combine each other_term with all date_exprs
                    # e.g. (other_term AND date_expr...) or (OR-based) depending on node.data
                    # For simplicity, treat them as AND if node.data == 'and_expr',
                    # or OR if node.data == 'or_expr'.
                    combined_data = node.data  # 'and_expr' or 'or_expr'
                    for ot in other_terms:
                        combined_children = [ot] + date_exprs
                        combined_node = Tree(combined_data, combined_children)
                        # Decompose further if needed
                        subqueries.extend(QueryProcessor._decompose_query(
                            combined_node, max_depth, current_depth + 1
                        ))
                else:
                    # Only date_exprs, no normal terms -> not valid alone
                    if QueryProcessor._is_valid_subquery(node):
                        return [node]
                    else:
                        return []
            else:
                # No date_exprs, just normal terms (or parentheses)
                # Recurse deeper
                for ot in other_terms:
                    subqueries.extend(QueryProcessor._decompose_query(ot, max_depth, current_depth + 1))

            return subqueries

        elif isinstance(node, Tree) and node.data == "expr":
            # expr: normal_expr ( "AND" date_expr )*
            # Children might be: normal_expr, ["AND", date_expr, "AND", date_expr, ...]
            # We can check each date_expr separately if we haven't exceeded max_depth.
            # If we have normal_expr plus multiple date_expr, we might produce subqueries combining them.
            subqueries = []

            # The first child is normal_expr
            normal_expr_node = node.children[0]
            # Decompose normal_expr node
            subqueries.extend(QueryProcessor._decompose_query(
                normal_expr_node, max_depth, current_depth
            ))

            # Then pairs of "AND" + date_expr
            i = 1
            while i < len(node.children):
                and_tok = node.children[i]  # "AND" (a Token)
                date_node = node.children[i + 1]  # date_expr (a Tree)
                i += 2

                # If not beyond depth, we can try decomposing the date_expr alone
                # But a single date_expr is not valid, so we won't return that alone
                if current_depth < max_depth:
                    subqueries.extend(QueryProcessor._decompose_query(
                        date_node, max_depth, current_depth + 1
                    ))
                else:
                    # If it's a date_expr but we reached max depth -> we keep it in combination
                    # If the combination is valid, return it as a subquery
                    combined_node = Tree('expr', [normal_expr_node, and_tok, date_node])
                    if QueryProcessor._is_valid_subquery(combined_node):
                        subqueries.append(combined_node)

            # If no subqueries were formed, check if node itself is valid as a subquery
            # because sometimes we might not have needed decomposition
            if not subqueries and QueryProcessor._is_valid_subquery(node):
                return [node]

            return subqueries

        else:
            # For other node types: field_term, normal_term, "(" expr ")", date_expr, etc.
            # If it contains a date_expr and we're not at max depth, we keep decomposing children.
            if QueryProcessor._contains_date_expr(node) and current_depth < max_depth:
                subqueries = []
                if isinstance(node, Tree):
                    for child in node.children:
                        subqueries.extend(QueryProcessor._decompose_query(child, max_depth, current_depth + 1))
                else:
                    # Leaf node
                    if QueryProcessor._is_valid_subquery(node):
                        subqueries.append(node)
                return subqueries
            else:
                # No further decomposition. Return if valid, else []
                if QueryProcessor._is_valid_subquery(node):
                    return [node]
                else:
                    return []

    @staticmethod
    def _is_single_date_expr(node: Tree) -> bool:
        """
        Determine if the given tree node represents a single date expression.

        This is used to identify invalid subqueries that consist of only date expressions.

        :param node: Tree node to check.
        :return: True if the node is a single date expression, False otherwise.
        """
        if isinstance(node, Tree):
            if node.data == 'date_expr':
                return True
            # If it has exactly one child, we can check recursively
            if len(node.children) == 1:
                return QueryProcessor._is_single_date_expr(node.children[0])
        return False

    @staticmethod
    def _is_date_expr(node) -> bool:
        """
        Check if the given tree node represents a date expression.

        :param node: The tree node to check.
        :return: True if the node is a date expression, False otherwise.
        """
        return isinstance(node, Tree) and node.data == 'date_expr'

    @staticmethod
    def _contains_date_expr(node) -> bool:
        """
        Check if the given node or any of its descendants contains a date expression.

        :param node: The tree node to check.
        :return: True if a date expression is found, False otherwise.
        """
        if QueryProcessor._is_date_expr(node):
            return True
        elif isinstance(node, Tree):
            return any(QueryProcessor._contains_date_expr(child) for child in node.children)
        else:
            return False

    @staticmethod
    def _is_valid_subquery(node) -> bool:
        """
        Determine if the given tree node represents a valid subquery.

        A subquery is valid if it contains at least one normal term and is not solely a date expression.

        :param node: The tree node to check.
        :return: True if the node is a valid subquery, False otherwise.
        """
        # 1) If it's a single date_expr -> invalid
        if QueryProcessor._is_single_date_expr(node):
            return False

        # 2) Must have at least one normal_term
        if not QueryProcessor._tree_contains_normal_term(node):
            return False

        return True

    @staticmethod
    def _tree_contains_normal_term(node) -> bool:
        """
        Check if the given node or any of its descendants contains a normal term.

        A normal term is a key component of a valid subquery.

        :param node: The tree node to check.
        :return: True if a normal term is found, False otherwise.
        """
        if isinstance(node, Tree):
            if node.data == 'normal_term':
                return True
            # Recurse on children
            return any(QueryProcessor._tree_contains_normal_term(child) for child in node.children)
        else:
            return False  # Leaf token, not a normal_term
