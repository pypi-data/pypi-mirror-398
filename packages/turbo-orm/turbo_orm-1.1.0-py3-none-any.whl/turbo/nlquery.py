"""
Natural Language Queries - Ask Your Database in English

Convert natural language to database queries using pattern matching.
Makes the ORM accessible to non-technical users.
"""

import re
from datetime import datetime, timedelta


class NaturalLanguageQuery:
    """Convert English to database queries"""

    PATTERNS = [
        # Find/Get patterns
        (r"find (?:all )?(\w+)s? (?:who|that|with) (.+)", "filter"),
        (r"get (?:all )?(\w+)s?(?: where (.+))?", "filter"),
        (r"show me (?:all )?(\w+)s?(?: (.+))?", "filter"),
        # Count patterns
        (r"how many (\w+)s? (.+)", "count"),
        (r"count (\w+)s?(?: (.+))?", "count"),
        # Specific lookups
        (r"find (\w+) (?:with|where) (\w+) (?:is|=) (.+)", "specific"),
    ]

    OPERATORS = {
        "greater than": "__gt",
        "more than": "__gt",
        "less than": "__lt",
        "fewer than": "__lt",
        "at least": "__gte",
        "at most": "__lte",
        "equal to": "",
        "equals": "",
        "is": "",
        "contains": "__contains",
        "starts with": "__startswith",
        "ends with": "__endswith",
    }

    TIME_PATTERNS = {
        "today": lambda: datetime.now().replace(hour=0, minute=0, second=0),
        "yesterday": lambda: datetime.now() - timedelta(days=1),
        "last week": lambda: datetime.now() - timedelta(weeks=1),
        "last month": lambda: datetime.now() - timedelta(days=30),
        "this year": lambda: datetime.now().replace(month=1, day=1),
    }

    def __init__(self, model_class):
        self.model_class = model_class

    def parse(self, query_text):
        """Parse natural language query"""
        query_text = query_text.lower().strip()

        for pattern, query_type in self.PATTERNS:
            match = re.match(pattern, query_text)
            if match:
                return self._build_query(query_type, match.groups())

        raise ValueError(f"Could not parse query: {query_text}")

    def _build_query(self, query_type, groups):
        """Build database query from parsed components"""
        filters = {}

        if query_type == "filter":
            model_hint, conditions = groups if len(groups) == 2 else (groups[0], None)
            if conditions:
                filters = self._parse_conditions(conditions)

        elif query_type == "count":
            model_hint, conditions = groups
            if conditions:
                filters = self._parse_conditions(conditions)

        elif query_type == "specific":
            model_hint, field, value = groups
            filters = {field: value.strip()}

        return {"type": query_type, "filters": filters}

    def _parse_conditions(self, conditions_text):
        """Parse conditions like 'active and from California and signed up last month'"""
        filters = {}

        # Split by 'and'
        conditions = [c.strip() for c in conditions_text.split(" and ")]

        for condition in conditions:
            # Try to extract field, operator, value
            for op_text, op_suffix in self.OPERATORS.items():
                if op_text in condition:
                    parts = condition.split(op_text)
                    if len(parts) == 2:
                        field = parts[0].strip().replace(" ", "_")
                        value = parts[1].strip()

                        # Parse value
                        if value.isdigit():
                            value = int(value)
                        elif value.replace(".", "").isdigit():
                            value = float(value)
                        elif value in ["true", "yes"]:
                            value = True
                        elif value in ["false", "no"]:
                            value = False
                        elif value in self.TIME_PATTERNS:
                            value = self.TIME_PATTERNS[value]()

                        key = field + op_suffix if op_suffix else field
                        filters[key] = value
                        break
            else:
                # Simple 'field value' format or just a field name
                if " " in condition:
                    field, value = condition.split(" ", 1)
                    field = field.strip().replace(" ", "_")
                    filters[field] = value.strip()
                else:
                    # Assume it's a boolean field
                    field = condition.replace(" ", "_")
                    filters[field] = True

        return filters

    def execute(self, db, query_text):
        """Execute natural language query"""
        parsed = self.parse(query_text)

        if parsed["type"] == "count":
            return self.model_class.count(db, **parsed["filters"])
        else:
            return self.model_class.filter(db, **parsed["filters"])


def add_nlq_to_model():
    """Add natural language query to Model"""
    from .model import Model

    @classmethod
    def ask(cls, db, question):
        """Ask a question in natural language"""
        nlq = NaturalLanguageQuery(cls)
        return nlq.execute(db, question)

    Model.ask = ask
