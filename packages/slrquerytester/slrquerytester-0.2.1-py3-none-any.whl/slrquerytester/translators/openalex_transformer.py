from .base_transformer import BaseTransformer
from .. import logger


class OpenAlexTransformer(BaseTransformer):
    """
    A Lark Transformer that translates a parsed query from the common query language
    into an OpenAlex-specific filter string.

    **Field Mapping** to OpenAlex:
       - title      -> title.search
       - abstract   -> abstract.search
       - fulltext   -> fulltext.search
       - keywords   -> keywords.keyword
       - address    -> raw_affiliation_strings.search
       - all_fields -> default.search
       - author     -> None

    **Logical Operators** in OpenAlex:
       - **AND**: Filters are joined by commas, e.g. `filter=title.search:dog,abstract.search:cat`.
       - **NOT**: Represented by prefixing the filter value with `!`, e.g. `abstract.search:!cat`.
       - **OR**: OpenAlex supports OR only within a single field or among certain field combinations {title, abstract, fulltext}.
       If an OR group has multiple fields from that set, we combine them into `title_and_abstract.search` or `default.search`
       as needed. If a negation or incompatible fields appear in an OR, a `ValueError` is raised.

    The transformer returns a string: openalex_filter_string
    """

    OR_COMPATIBLE_FIELDS = {'title', 'abstract', 'fulltext'}
    FIELD_MAP = {
        'title': 'title.search',
        'abstract': 'abstract.search',
        'fulltext': 'fulltext.search',
        'keywords': 'keywords.keyword',
        'author': None,
        'address': 'raw_affiliation_strings.search',
        'all_fields': 'default.search'
    }

    def start(self, children):
        """
        Entry point of the parse tree.
        Typically children => [list_of_conditions], combine them with commas in _combine_conditions.
        """
        # We can do a small check if 'children[0]' is a list of conditions.
        if not children:
            # no conditions
            raise ValueError("Something strange has happened: None of the conditions were interpreted as filters!")
        top_result = children[0]
        if isinstance(top_result, list):
            conditions = top_result
        else:
            conditions = []
        return self._combine_conditions(conditions)

    @staticmethod
    def _combine_conditions(conditions):
        """
        Convert list of (attr, neg, val) => 'attr:val' or 'attr:!val'
        joined by commas
        """
        if not conditions:
            return ""
        parts = []
        for (attr, neg, val) in conditions:
            if neg:
                parts.append(f"{attr}:!{val}")
            else:
                parts.append(f"{attr}:{val}")
        return ",".join(parts)

    def or_expr(self, children):
        """
        or_expr => possible multiple condition-lists joined by OR.
        If multiple fields are from {title, abstract, fulltext}, we unify them;
        else raise ValueError or unify into default.search if the grammar allows it.
        """
        cond_lists = []
        i = 0
        while i < len(children):
            ch = children[i]
            # skip "OR" tokens
            if isinstance(ch, str) and ch.upper() in ["OR", "||"]:
                i += 1
                continue
            # if it's a list, that's a sub-expression's conditions
            if isinstance(ch, list):
                cond_lists.append(ch)
            i += 1

        # Filter out empty sub-lists
        cond_lists = [lst for lst in cond_lists if lst]

        if not cond_lists:
            # all sides empty => no conditions
            return []

        if len(cond_lists) == 1:
            # only one side => no actual OR
            return cond_lists[0]

        # multiple sub-lists => unify them
        all_conditions = []
        for group in cond_lists:
            all_conditions.extend(group)

        # If any neg => error
        if any(c[1] for c in all_conditions):
            raise ValueError("OpenAlex does not support OR with negation.")

        # Filter out ignored fields
        all_conditions = [c for c in all_conditions if self._is_supported(c[0])]
        if not all_conditions:
            return []

        attributes = {c[0] for c in all_conditions}
        # e.g. 'title.search' => 'title'
        field_names = set(a.split('.')[0] for a in attributes if '.' in a) | {a for a in attributes if '.' not in a}
        values = [c[2] for c in all_conditions]
        if len(attributes) > 1:
            # multiple attributes => check if they're all in {title,abstract,fulltext}
            if field_names.issubset(self.OR_COMPATIBLE_FIELDS):
                combined_attr = self._combine_compatible_fields(field_names)
                return [(combined_attr, False, '|'.join(values))]
            else:
                logger.warning("OpenAlex does not support OR across incompatible fields. Defaulted to default.search")
                return [('default.search', False, '|'.join(values))]
        else:
            # single attribute => just join values with '|'
            attr = attributes.pop()
            if len(values) == 1:
                return [(attr, False, values[0])]
            return [(attr, False, '|'.join(values))]

    @staticmethod
    def _is_supported(attr):
        return attr is not None and attr.strip()

    def _combine_compatible_fields(self, field_names):
        """
        If user typed OR among {title, abstract, fulltext},
        combine them into 'title_and_abstract.search' or 'default.search'.
        """
        if len(field_names) == 1:
            f = field_names.pop()
            return self.FIELD_MAP[f]
        elif len(field_names) == 2:
            # e.g. {title, abstract} => title_and_abstract.search
            # otherwise => default.search
            if field_names == {'title', 'abstract'}:
                return 'title_and_abstract.search'
            return 'default.search'
        else:
            # 3 => default
            return 'default.search'

    def and_expr(self, children):
        """
        and_expr -> combine sub-lists with no special logic.
        Produce a single list that merges them, as AND is just a comma (list) in OpenAlex.
        """
        conds = []
        for c in children:
            if isinstance(c, list):
                conds.extend(c)
        return conds

    def paren_expr(self, children):
        """
        Typically children => [list_of_conditions].
        If so, just return that list (ignore parentheses).
        """
        if len(children) == 1 and isinstance(children[0], list):
            # child is the condition list from or_expr
            return children[0]
        # fallback: if it's a single string or no children
        if len(children) == 1:
            return children[0]
        return []

    def NOT(self, token):
        return "NOT"

    def field_term(self, children):
        """
        We want a list of (attr, neg, val).
        If we see 'NOT' token followed by a child list => we set neg=True on them.
        """
        conds = []
        i = 0
        while i < len(children):
            ch = children[i]
            if isinstance(ch, list):
                # a normal or date expression => just add
                conds.extend(ch)
            elif isinstance(ch, str):
                # could be 'AND', 'NOT', etc.
                if ch.upper() == "NOT":
                    # next child should be a list => make them neg
                    if i+1 < len(children) and isinstance(children[i+1], list):
                        for (attr, neg, val) in children[i+1]:
                            conds.append((attr, True, val))
                        i += 2
                        continue
            i += 1
        return conds

    def normal_expr(self, children):
        conds = []
        for c in children:
            if isinstance(c, list):
                conds.extend(c)
        return conds

    def normal_term(self, children):
        """
        [FIELD, ':', VALUE] => produce [(mapped_attr, False, 'value')]
        If field is author => ignore.
        """
        if len(children) != 3:
            raise ValueError(f"Something weird has happened: {children} was parsed as normal_term!")

        field, operator, val_raw = children
        if operator != ":":
            raise ValueError(f"Something weird has happened: {operator} was parsed as normal_op!")
        if field == 'publication_year':
            raise ValueError(f"Something weird has happened: {field} was parsed as normal_term!")
        val_str = val_raw.strip('"')

        mapped = self.FIELD_MAP.get(field, None)
        if not mapped:
            return []
        else:
            return [(mapped, False, f'"{val_str}"')]

    def date_expr(self, children):
        if len(children) != 3:
            raise ValueError(f"Something weird has happened: {children} was parsed as date_expr!")
        field, operator, year_str = children
        year_str = year_str.strip('"')
        try:
            year_int = int(year_str)
        except ValueError:
            raise ValueError(f"Something weird has happened: {year_str} was parsed as year!")

        if field != 'publication_year':
            raise ValueError(f"Something weird happened: {field} was parsed as date_field!")

        if operator == ">=":
            return [('from_publication_date', False, f"{year_str}-01-01")]
        elif operator == "<=":
            return [('to_publication_date', False, f"{year_str}-12-31")]
        elif operator == ">":
            return [('from_publication_date', False, f"{year_int + 1}-01-01")]
        elif operator == "<":
            return [('to_publication_date', False, f"{year_int - 1}-12-31")]
        elif operator == "=":
            return [('publication_year', False, f"{year_str}")]
        else:
            raise ValueError(f"Something weird has happened: {operator} was parsed as date_op!")
