from .base_transformer import BaseTransformer

class CORETransformer(BaseTransformer):
    """
    A Lark Transformer that converts a parsed query (from the new grammar)
    into a CORE API-specific query syntax string.

    **Field Mapping** to CORE:
      - title           -> "title"
      - abstract        -> "abstract"
      - author          -> "authors"
      - keywords        -> ""
      - fulltext        -> "fullText"
      - address         -> None
      - all_fields      -> None

    The transformer returns a string: core_query_string
    """

    FIELD_MAP = {
        "title": "title",
        "abstract": "abstract",
        "author": "authors",
        "keywords": "fullText",
        "fulltext": "fullText",
        "publication_year": "yearPublished",
        "all_fields": "fullText"
    }

    def __init__(self):
        super().__init__()
        self.found_valid_normal_term = None

    def start(self, children):
        """
        The base class returns a single string from children.
        We then strip leading 'AND ' or 'OR ' if present.
        """
        query = super().start(children).strip()
        # Remove leading "AND " or "OR " if present
        up = query.upper()
        if up.startswith("AND "):
            query = query[4:].strip()
        elif up.startswith("OR "):
            query = query[3:].strip()
        if not self.found_valid_normal_term:
            raise ValueError("CORETransformer: No valid normal terms found (all unsupported?), query invalid.")
        return query

    def or_expr(self, children):
        """
        Base class merges with spaces => might leave trailing "OR " if second subexpr was empty.
        We'll re-process children to produce "(expr) OR (expr)" only if they are non-empty.
        """
        # We'll gather sub-expressions, ignoring literal 'OR' tokens or empty pieces
        subexprs = []
        i = 0
        while i < len(children):
            piece = children[i]
            if isinstance(piece, str):
                up = piece.upper().strip()
                if up in ("OR", "||"):
                    i += 1
                    continue
                # else if not empty, we keep it
                trimmed = piece.strip()
                if trimmed:
                    subexprs.append(trimmed)
            else:
                # e.g. a list or something from base that turned into string
                txt = str(piece).strip()
                if txt:
                    subexprs.append(txt)
            i += 1

        if not subexprs:
            return ""

        if len(subexprs) == 1:
            return subexprs[0]

        # else build "(prev) OR (next)" style
        result = subexprs[0]
        for idx in range(1, len(subexprs)):
            result = f"{result} OR {subexprs[idx]}"
        return result

    def normal_term(self, children):
        if len(children) != 3:
            raise ValueError(f"Something weird has happened: {children} was parsed as date_expr")
        field, operator, val_raw = children
        if operator != ":":
            raise ValueError(f"Something weird has happened: {operator} was parsed as normal_op!")
        if field == 'publication_year':
            raise ValueError(f"Something weird has happened: {field} was parsed as normal_term!")
        val_str = val_raw.strip('"')
        core_field = self.FIELD_MAP.get(str(field), None)
        if core_field:
            self.found_valid_normal_term = True
            return f'{core_field}:"{val_str}"'
        return ""

    def date_expr(self, children):
        """
        e.g. publication_year >= 2020 => 'PUBYEAR > 2019'
        (like your original code).
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
        pubyear_field = "yearPublished"
        return f'{pubyear_field} {operator} {year_int}'


    def NOT(self, token):
        """
        Grammar: NOT: "AND NOT" | "&!" | "NOT"
        In CORE, "AND NOT" isn't valid. We'll always produce "AND NOT".
        """
        return "AND NOT"

    def AND(self, token):
        """
        Grammar: AND: "AND" | "&&"
        In CORE, "&&" isn't valid. We'll always produce "AND".
        """
        return "AND"

    def OR(self, token):
        """
        Grammar: OR: "OR" | "||"
        In CORE, "||" isn't valid. We'll always produce "OR".
        """
        return "OR"
