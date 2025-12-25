import re

from .base_transformer import BaseTransformer


class DimensionsTransformer(BaseTransformer):
    """
    A Lark Transformer that converts a parsed query (from the new grammar)
    into the Dimensions-specific DSL query syntax.

    **Field Mapping** to Dimensions:
        - title            -> "title_only"
        - abstract         -> "abstract"
        - author           -> "authors"
        - keywords         -> "concepts"
        - fulltext         -> "full_data_exact"
        - address          -> "research_org_countries"
        - all_fields       -> "full_data"

    **Date Handling**:
    All the date constraints are removed from the string, and ultimately the largest duration that satisfies all the
    date constraints is created.

    The transformer returns a string: dimensions_query_string
    """

    FIELD_MAP = {
        "title": "title_only",
        "abstract": "abstract",
        "author": "authors",
        "keywords": "concepts",
        "fulltext": "full_data_exact",
        "address": "research_org_countries",
        "all_fields": "full_data"
    }

    def __init__(self):
        super().__init__()
        self.start_year = None
        self.stop_year = None

    def start(self, children):
        # Return the final DSL by calling generate_query
        filters = []
        if self.start_year is not None:
            filters.append(f"year>={self.start_year}")
        if self.stop_year is not None:
            filters.append(f"year<={self.stop_year}")

        filters_clause = ""
        if filters:
            filters_clause = "where " + " and ".join(filters)

        # The main (transformed) query content
        query_clause = children[0] if children[0] else ""

        # Return fields for Dimensions DSL
        return_fields = [
            "title", "authors", "doi", "year", "abstract",
            "linkout", "concepts", "journal", "date",
            "proceedings_title", "book_title", "publisher",
            "pages", "book_series_title", "book_doi"
        ]
        return_clause = (
            f"return publications[{'+'.join(return_fields)}]"
            if return_fields else ""
        )
        # Combine everything into a single DSL
        if filters_clause:
            return f"search publications {query_clause.strip()} {filters_clause.strip()} {return_clause.strip()}"
        return f"search publications {query_clause.strip()} {return_clause.strip()}"

    def and_expr(self, children):
        """
        Skip 'AND' if next child is empty => no trailing AND
        """
        parts = []
        i = 0
        while i < len(children):
            c = children[i]
            c_str = self.transform(c) if hasattr(c, 'children') else str(c)

            if c_str.upper() == "AND":
                if i + 1 < len(children):
                    n_c = children[i + 1]
                    n_str = self.transform(n_c) if hasattr(n_c, 'children') else str(n_c)
                    if not n_str.strip():
                        # skip both
                        i += 2
                        continue
                parts.append(c_str)
            else:
                if c_str.strip():
                    parts.append(c_str)
            i += 1
        return " ".join(parts).strip()

    def field_term(self, children):
        """
        The base class typically just joins children. We'll do that,
        but afterwards we remove any trailing operator if it’s followed only by empty date_expr.
        """
        # if our last child was a date_expr => empty string => leftover operator at end?
        str_parts = []
        i = 0
        while i < len(children):
            child = children[i]
            child_str = self.transform(child) if hasattr(child, 'children') else str(child)
            # if child is a token AND or NOT or OR:
            # or child is date_expr => ""

            if child_str.upper() in ["AND", "OR", "NOT"]:
                # check next child
                if i + 1 < len(children):
                    next_child = children[i + 1]
                    next_str = self.transform(next_child) if hasattr(next_child, 'children') else str(next_child)
                    if next_str == "":
                        # next child is a date_expr that yields "", so skip appending this operator
                        # and skip next child
                        i += 2
                        continue
                str_parts.append(child_str)
            else:
                # normal text chunk or empty
                if child_str:
                    str_parts.append(child_str)
            i += 1

        # Now build final from str_parts
        final = " ".join(str_parts).strip()

        return final

    def date_expr(self, children):
        """
        Instead of returning the original date expression text,
        we store start/stop years. Return "" so it doesn't appear in the final wos_str.
        """
        if len(children) != 3:
            return ""
        field, operator, val = children

        if field == "publication_year":
            year = int(val)
            if operator == ">=":
                if self.start_year is None or year > self.start_year:
                    self.start_year = year
            elif operator == "<=":
                if self.stop_year is None or year < self.stop_year:
                    self.stop_year = year
            elif operator == "=":
                self.start_year = year
                self.stop_year = year
            elif operator == ">":
                # year+1
                actual_start = year + 1
                if self.start_year is None or actual_start > self.start_year:
                    self.start_year = actual_start
            elif operator == "<":
                # year-1
                actual_stop = year - 1
                if self.stop_year is None or actual_stop < self.stop_year:
                    self.stop_year = actual_stop
            return ""

    def normal_term(self, children):
        """
        Override the base method that originally returns e.g. "title:Hello".
        Now we produce WoS: "TI=(Hello)".
        """
        if len(children) != 3:
            raise ValueError(f"Something weird has happened: {children} was parsed as date_expr")
        field, operator, val_raw = children
        if operator != ":":
            raise ValueError(f"Something weird has happened: {operator} was parsed as normal_op!")
        if field == 'publication_year':
            raise ValueError(f"Something weird has happened: {field} was parsed as normal_term!")
        val_str = val_raw.strip('"')
        dimensions_field = self.FIELD_MAP.get(field, field.upper())
        return f'in {dimensions_field} for "{val_str}"'

    @staticmethod
    def escape_special_characters(value: str) -> str:
        special_chars = r'^":~\[\]{}()!|&+'
        return re.sub(f"([{re.escape(special_chars)}])", r"\\\1", value)

    def NOT(self, token):
        """
        Grammar: NOT: "AND NOT" | "&!" | "NOT"
        In WoS, "AND NOT" isn't valid. We'll always produce "NOT".
        """
        return "NOT"

    def AND(self, token):
        """
        Grammar: NOT: "AND NOT" | "&!" | "NOT"
        In WoS, "AND NOT" isn't valid. We'll always produce "NOT".
        """
        return "AND"

    def OR(self, token):
        """
        Grammar: NOT: "AND NOT" | "&!" | "NOT"
        In WoS, "AND NOT" isn't valid. We'll always produce "NOT".
        """
        return "OR"