from .base_transformer import BaseTransformer


class IEEETransformer(BaseTransformer):
    """
    A Lark Transformer that translates a parsed query from the common query language
    into a IEEE-specific query syntax string.

    **Field Mapping** to IEEE:
        - title       -> Document Title
        - abstract    -> Abstract
        - author      -> Authors
        - keywords    -> Author Keywords
        - fulltext    -> Full Text Only
        - address     -> Author Affiliations
        - all_fields  -> Full Text & Metadata

    **Date Handling**:
    All the date constraints are removed from the string, and ultimately the largest duration that satisfies all the
    date constraints is created.

    The transformer returns a tuple: (ieee_query_string, start_year, stop_year).
    """

    field_map = {
        "title": "\"Document Title\"",
        "abstract": "\"Abstract\"",
        "author": "\"Authors\"",
        "keywords": "\"Author Keywords\"",
        "fulltext": "\"Full Text Only\"",
        "address": "\"Author Affiliations\"",
        "all_fields": "\"Full Text & Metadata\""
    }

    def __init__(self):
        super().__init__()
        self.start_year = None
        self.stop_year = None

    def start(self, children):
        return super().start(children), self.start_year, self.stop_year

    def normal_term(self, children):
        if len(children) != 3:
            raise ValueError(f"Something weird has happened: {children} was parsed as date_expr")
        field, operator, val_raw = children
        if operator != ":":
            raise ValueError(f"Something weird has happened: {operator} was parsed as normal_op!")
        if field == 'publication_year':
            raise ValueError(f"Something weird has happened: {field} was parsed as normal_term!")
        val_str = val_raw.strip('"')
        ieee_field = self.field_map.get(field, field.upper())
        return f'{ieee_field}:"{val_str}"'

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

    def date_expr(self, children):
        """
        Instead of returning the original date expression text,
        we store start/stop years. Return "" so it doesn't appear in the final wos_str.
        """
        if len(children) != 3:
            raise ValueError(f"Something weird has happened: {children} was parsed as date_expr")

        field, operator, year_str = children
        if field != 'publication_year':
            raise ValueError(f"Something weird happened: {field} was parsed as date_field!")
        # remove quotes if present
        year_str = year_str.strip('"')
        try:
            year_int = int(year_str)
        except ValueError:
            raise ValueError(f"Something weird has happened: An unknown YEAR {year_str} was successfully parsed!")

        if operator == ">=":
            if self.start_year is None or year_int > self.start_year:
                self.start_year = year_int
        elif operator == ">":
            if self.start_year is None or year_int >= self.start_year:
                self.start_year = year_int + 1
        elif operator == "<=":
            if self.stop_year is None or year_int < self.stop_year:
                self.stop_year = year_int
        elif operator == "<":
            if self.stop_year is None or year_int <= self.stop_year:
                self.stop_year = year_int - 1
        elif operator == "=":
            self.start_year = year_int
            self.stop_year = year_int
        else:
            raise ValueError(f"Something weird has happened: {operator} was parsed as date_op!")
        return ""

    def NOT(self, token):
        """
        Grammar: NOT: "AND NOT" | "&!" | "NOT"
        In IEEE, "AND NOT" isn't valid. We'll always produce "NOT".
        """
        return "NOT"

    def AND(self, token):
        """
        Grammar: NOT: "AND NOT" | "&!" | "NOT"
        In IEEE, "AND NOT" isn't valid. We'll always produce "NOT".
        """
        return "AND"

    def OR(self, token):
        """
        Grammar: NOT: "AND NOT" | "&!" | "NOT"
        In IEEE, "AND NOT" isn't valid. We'll always produce "NOT".
        """
        return "OR"
