from datetime import datetime

from .base_transformer import BaseTransformer


class LENSTransformer(BaseTransformer):
    """
        A Lark Transformer that translates a parsed query from the common query language
        into a LENS-specific query syntax string.

        **Field Mapping** to LENS:
           - title       -> title
           - abstract    -> abstract
           - author      -> author.displayname
           - keywords    -> keyword (case-sensitive)
           - fulltext    -> full_text
           - address     -> author.affiliation.name_original
           - all_fields  -> '' (interpreted as free-text search)

        The transformer returns a string: lens_query_string
        """

    field_map = {
        "title": "title",
        "abstract": "abstract",
        "author": "author.displayname",
        "keywords": "keyword",
        "fulltext": "full_text",
        "address": "author.affiliation.name_original",
        "all_fields": ""
    }

    def normal_term(self, children):
        """
        base_transformer => 'title:Hello'
        We produce e.g. 'TITLE("Hello")' with the scopus field map.
        """
        if len(children) != 3:
            raise ValueError(f"Something weird has happened: {str(children)} was parsed as normal_term")
        field, operator, val_raw = children
        if operator != ":":
            raise ValueError(f"Something weird has happened: {operator} was parsed as normal_op!")
        if field == 'publication_year':
            raise ValueError(f"Something weird has happened: {field} was parsed as normal_term!")
        val_str = val_raw.strip('"')
        lens_field = self.field_map.get(str(field), str(field).upper())
        if lens_field:
            return f'{lens_field}:({val_str})'
        else:
            return f'({val_str})'

    def date_expr(self, children):
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
        pubyear_field = "year_published"

        if operator == '=':
            return f'{pubyear_field}:{year_str}'
        elif operator == '>=':
            return f'{pubyear_field}:[{year_str} TO {datetime.now().year}]'
        elif operator == '<=':
            return f'{pubyear_field}:[0001 TO {year_str}]'
        elif operator == '>':
            return f'{pubyear_field}:[{year_int + 1} TO {datetime.now().year}]'
        elif operator == '<':
            return f'{pubyear_field}:[0001 TO {year_int - 1}]'
        else:
            raise ValueError(f"Something weird has happened: {operator} was parsed as date_op!")

    def NOT(self, token):
        """
        Grammar: NOT: "AND NOT" | "&!" | "NOT"
        In LENS, "AND NOT" isn't valid. We'll always produce "AND NOT".
        """
        return "NOT"

    def AND(self, token):
        """
        Grammar: AND: "AND" | "&&"
        In LENS, "&&" isn't valid. We'll always produce "AND".
        """
        return "AND"

    def OR(self, token):
        """
        Grammar: OR: "OR" | "||"
        In LENS, "||" isn't valid. We'll always produce "OR".
        """
        return "OR"
