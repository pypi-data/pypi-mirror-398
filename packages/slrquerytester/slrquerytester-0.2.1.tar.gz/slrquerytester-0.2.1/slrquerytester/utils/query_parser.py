"""
.. include:: ../../docs/language.md
"""

from lark import Lark, Tree


_query_grammar = r"""
start: or_expr

or_expr: and_expr (OR and_expr)*

and_expr: field_term (AND field_term)*

field_term: (normal_expr|paren_expr) (AND date_expr)* (NOT (normal_expr|paren_expr))? (AND date_expr)* 
          | date_expr

normal_expr: normal_term ((AND|OR) normal_term)*

paren_expr: "(" or_expr ")"

date_expr: DATE_FIELD DATE_OP INT

normal_term: NORMAL_FIELD TEXT_OP VALUE

AND: "AND" | "&&"
OR: "OR" | "||"
NOT: "AND NOT" | "&!" | "NOT"

# Operators
DATE_OP: ">=" | "<=" | "=" | ">" | "<"
TEXT_OP: ":"

# Fields
NORMAL_FIELD: "title" | "abstract" | "fulltext" | "keywords" 
            | "author" | "address" | "all_fields"
DATE_FIELD: "publication_year"

# Values
VALUE: ESCAPED_STRING | WORD

%import common.WORD
%import common.INT
%import common.ESCAPED_STRING
%import common.WS
%ignore WS
"""

# Create the parser
_parser = Lark(_query_grammar, start='start')

def _validate_has_normal_term(parse_tree):
    """
    Traverse the parse tree. If we find at least one 'normal_term', okay.
    Otherwise, raise an error.
    """
    if isinstance(parse_tree, Tree):
        if parse_tree.data == 'normal_term':
            return True  # Found a normal term
        # else check children
        for child in parse_tree.children:
            if _validate_has_normal_term(child):
                return True
        return False
    else:
        # It's a Token, not a Tree, no normal_term here
        return False

def parse_with_semantic_check(query):
    parse_tree = _parser.parse(query)
    if not _validate_has_normal_term(parse_tree):
        raise ValueError("Query must contain at least one normal term (e.g. title:..., author:..., etc.)")
    return parse_tree