from abc import ABC

from .base_transformer import BaseTransformer


class SpringerBaseTransformer(BaseTransformer, ABC):
    """
    An abstract Lark Transformer that translates a parsed query from the common query language
    into a Springer-specific query syntax string.
    It depends on its subclasses to define a field map.

    The transformer returns a string: springer_query_string
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Subclasses can define their own field_map
        self.FIELD_MAP = {}

    def start(self, children):
        return f"({super().start(children).strip()})"

    def normal_term(self, children):
        """
        Overridden to map fields using self.field_map
        or treat it as free text if map is blank.
        base_transformer returns e.g. "title:Hello"
        We'll parse that into field + value, then produce 'title:"Hello"' or just '"Hello"' for free text.
        """
        if len(children) != 3:
            raise ValueError(f"Something weird has happened: {children} was parsed as normal_term")

        field, operator, val_raw = children
        if operator != ":":
            raise ValueError(f"Something weird has happened: {operator} was parsed as normal_op!")
        if field == 'publication_year':
            raise ValueError(f"Something weird has happened: {field} was parsed as normal_term!")
        val_str = val_raw.strip('"')

        springer_field = self.FIELD_MAP.get(field, None)
        if springer_field:
            # e.g. 'title:"heart attack"'
            return f'{springer_field}:"{val_str}"'
        else:
            # free text => if multi-word, wrap in quotes
            return f'"{val_str}"'

    def date_expr(self, children):
        if len(children) != 3:
            raise ValueError(f"Something weird has happened: {children} was parsed as date_expr")

        field, operator, year_str = children
        if field != "publication_year":
            raise ValueError(f"Something weird happened: {field} was parsed as date_field!")
        # remove quotes if present
        year_str = year_str.strip('"')
        try:
            year_int = int(year_str)
        except ValueError:
            raise ValueError(f"Something weird has happened: An unknown YEAR {year_str} was successfully parsed!")

        if operator == "=":
            return f'datefrom:"{year_str}-01-01" AND dateto:"{year_str}-12-31"'
        elif operator == ">=":
            return f'datefrom:"{year_str}-01-01"'
        elif operator == ">":
            if year_int is not None:
                return f'datefrom:"{year_int + 1}-01-01"'
        elif operator == "<=":
            return f'dateto:"{year_str}-12-31"'
        elif operator == "<":
            if year_int is not None:
                return f'dateto:"{year_int - 1}-12-31"'
        else:
            raise ValueError(f"Something weird has happened: {operator} was parsed as date_op!")

    def NOT(self, token):
        """
        Grammar: NOT: "AND NOT" | "&!" | "NOT"
        In Springer, "AND NOT" isn't valid. We'll always produce "NOT".
        """
        return "NOT"

    def AND(self, token):
        """
        Grammar: AND: "AND" | "&&"
        In Springer, "&&" isn't valid. We'll always produce "AND".
        """
        return "AND"

    def OR(self, token):
        """
        Grammar: OR: "OR" | "||"
        In Springer, "||" isn't valid. We'll always produce "OR".
        """
        return "OR"


class SpringerTransformerFree(SpringerBaseTransformer):
    """
    A Lark Transformer that translates a parsed query from the common query language
    into a Springer-specific query syntax string, within the Free quota of the API.

    **Field Mapping** to Springer-Free:
       - title      -> ''
       - abstract   -> ''
       - author     -> ''
       - keywords   -> keyword
       - fulltext   -> ''
       - address    -> ''
       - all_fields -> ''

    In the free version of the Springer API, all fields (except keywords)
    are effectively treated as free text. So we set them all to ''.

    The transformer returns a string: springer_query_string
    """

    def __init__(self):
        super().__init__()
        self.FIELD_MAP = {
            'title': '',
            'abstract': '',
            'keywords': 'keyword',
            'author': '',
            'address': '',
            'fulltext': '',
            'all_fields': ''
        }


class SpringerTransformerPremium(SpringerBaseTransformer):
    """
    A Lark Transformer that translates a parsed query from the common query language
    into a Springer-specific query syntax string, within the Premium quota of the API.

    **Field Mapping** to Springer-Premium:
       - title      -> title
       - abstract   -> ''
       - author     -> name
       - keywords   -> keyword
       - fulltext   -> ''
       - address    -> orgname
       - all_fields -> ''

    The transformer returns a string: springer_query_string
    """

    def __init__(self):
        super().__init__()
        self.FIELD_MAP = {
            'title': 'title',
            'abstract': '',
            'keywords': 'keyword',
            'author': 'name',
            'address': 'orgname',
            'fulltext': '',
            'all_fields': ''
        }
