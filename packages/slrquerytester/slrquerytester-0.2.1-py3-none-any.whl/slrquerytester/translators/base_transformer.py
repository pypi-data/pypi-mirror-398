from lark import Transformer

class BaseTransformer(Transformer):
    """
    Base transformer that reconstructs the *original* query string
    from the parse tree. This preserves parentheses, date expressions, etc.
    """
    @staticmethod
    def start(children):
        # 'start' -> or_expr
        return "".join(children) if children else ""

    def or_expr(self, children):
        # or_expr -> [and_expr, (OR, and_expr)*]
        # Typically children => something like ["title:Hello", "OR", "abstract:World"]
        return self._join_tokens(children, sep=" ")

    def and_expr(self, children):
        # and_expr -> [field_term, (AND, field_term)*]
        return self._join_tokens(children, sep=" ")

    def field_term(self, children):
        # field_term can be normal_expr + date_expr, or paren_expr, or date_expr alone
        return self._join_tokens(children, sep=" ")

    @staticmethod
    def paren_expr(children):
        # paren_expr: "(" or_expr ")"
        # children => [string_of_or_expr]
        inside = "".join(children)
        return f"({inside})"

    def normal_expr(self, children):
        # normal_expr -> [ normal_term, (AND|OR, normal_term)* ]
        return self._join_tokens(children, sep=" ")

    @staticmethod
    def normal_term(children):
        # [NORMAL_FIELD, TEXT_OP, VALUE]
        # e.g. ["title", ":", "Hello"]
        return "".join(children)

    @staticmethod
    def date_expr(children):
        # date_expr -> [DATE_FIELD, DATE_OP, INT]
        # e.g. ["publication_year", ">=", "2020"]
        return "".join(children)

    @staticmethod
    def AND(token):
        return token.value  # "AND" or "&&"

    @staticmethod
    def OR(token):
        return token.value  # "OR" or "||"

    @staticmethod
    def NOT(token):
        return token.value  # "NOT", or "AND NOT", etc.

    @staticmethod
    def TEXT_OP(token):
        return token.value  # ":"

    @staticmethod
    def DATE_OP(token):
        return token.value  # "=", ">=", "<="

    @staticmethod
    def NORMAL_FIELD(token):
        return token.value

    @staticmethod
    def DATE_FIELD(token):
        return token.value

    @staticmethod
    def WORD(token):
        return token.value

    @staticmethod
    def VALUE(children):
        # A rule that might encapsulate ESCAPED_STRING|WORD
        return "".join(children)

    @staticmethod
    def ESCAPED_STRING(token):
        return token.value  # e.g. "\"Hello World\""

    @staticmethod
    def INT(token):
        return token.value

    # Utility: join child strings with a specified separator
    @staticmethod
    def _join_tokens(children, sep=" "):
        # convert each child to string, if it's a list or single string
        str_parts = []
        for c in children:
            if isinstance(c, list):
                str_parts.append(" ".join(c))
            else:
                str_parts.append(str(c))
        return sep.join(str_parts)

    def __default__(self, data, children, meta):
        # fallback for unhandled rules
        if isinstance(children, list) and len(children) == 1:
            return children[0]
        return "".join(str(child) for child in children)
