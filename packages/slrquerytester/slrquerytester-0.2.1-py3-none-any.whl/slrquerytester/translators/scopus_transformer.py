from .base_transformer import BaseTransformer

class ScopusTransformer(BaseTransformer):
    """
    A Lark Transformer that converts a parsed query from the common query language
    into a Scopus-specific query syntax string.

    **Field Mapping** to Scopus:
       - title      -> TITLE
       - abstract   -> ABS
       - author     -> AUTHOR-NAME
       - keywords   -> KEY
       - fulltext   -> TITLE-ABS-KEY
       - address    -> AFFIL
       - all_fields -> ALL

    The transformer returns a string: scopus_query_string
    """

    FIELD_MAP = {
        'title': 'TITLE',
        'abstract': 'ABS',
        'keywords': 'KEY',
        'author': 'AUTHOR-NAME',
        'address': 'AFFIL',
        'fulltext': 'TITLE-ABS-KEY',
        'all_fields': 'ALL'
    }

    def normal_term(self, children):
        """
        base_transformer => 'title:Hello'
        We produce e.g. 'TITLE("Hello")' with the scopus field map.
        """
        # children => [NORMAL_FIELD, TEXT_OP, value]
        if len(children) != 3:
            raise ValueError(f"Something weird has happened: {str(children)} was parsed as normal_term")

        field, operator, val_raw = children
        if operator != ":":
            raise ValueError(f"Something weird has happened: {operator} was parsed as normal_op!")
        if field == 'publication_year':
            raise ValueError(f"Something weird has happened: {field} was parsed as normal_term!")
        val_str = val_raw.strip('"')

        scopus_field = self.FIELD_MAP.get(str(field), str(field).upper())
        return f'{scopus_field}("{val_str}")'

    def date_expr(self, children):
        if len(children) != 3:
            raise ValueError(f"Something weird has happened: {children} was parsed as date_expr")

        field, operator, int_str = children
        if field != 'publication_year':
            raise ValueError(f"Something weird happened: {field} was parsed as date_field!")
        # remove quotes if present
        year_str = int_str.strip('"')
        try:
            year_int = int(year_str)
        except ValueError:
            raise ValueError(f"Something weird has happened: An unknown YEAR {year_str} was successfully parsed!")
        pubyear_field = "PUBYEAR"

        if operator == '=':
            # exact year => PUBYEAR = year
            return f'{pubyear_field} = {year_str}'
        elif operator == '>=':
            # >= year => > (year - 1)
            return f'{pubyear_field} > {year_int - 1}'
        elif operator == '<=':
            # <= year => < (year + 1)
            return f'{pubyear_field} < {year_int + 1}'
        elif operator == '>':
            return f'{pubyear_field} > {year_str}'
        elif operator == '<':
            return f'{pubyear_field} < {year_str}'
        else:
            raise ValueError(f"Something weird has happened: {operator} was parsed as date_op!")

    def NOT(self, token):
        """
        Grammar: NOT: "AND NOT" | "&!" | "NOT"
        In Scopus, "AND NOT" isn't valid. We'll always produce "AND NOT".
        """
        return "AND NOT"

    def AND(self, token):
        """
        Grammar: AND: "AND" | "&&"
        In Scopus, "&&" isn't valid. We'll always produce "AND".
        """
        return "AND"

    def OR(self, token):
        """
        Grammar: OR: "OR" | "||"
        In Scopus, "||" isn't valid. We'll always produce "OR".
        """
        return "OR"