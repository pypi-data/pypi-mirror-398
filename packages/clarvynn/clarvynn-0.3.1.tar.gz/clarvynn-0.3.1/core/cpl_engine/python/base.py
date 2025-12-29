import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from pyparsing import (
    CaselessKeyword,
    Group,
    Literal,
    ParseException,
    QuotedString,
    Suppress,
    Word,
    alphanums,
    alphas,
    infixNotation,
    nums,
    opAssoc,
    pyparsing_common,
)


@dataclass
class RequestData:
    """Normalized request data format used across all adapters"""

    method: Optional[str] = None
    path: Optional[str] = None
    status_code: Optional[int] = None
    duration_ms: Optional[float] = None
    user_id: Optional[str] = None
    trace_id: Optional[str] = None
    span_name: Optional[str] = None
    span_kind: Optional[str] = None
    custom_attributes: Dict[str, Any] = field(default_factory=dict)


class CPLParser:
    """
    Complete CPL expression parser using pyparsing.

    Supports:
    - Comparison operators: ==, !=, <, <=, >, >=
    - String operators: contains, not contains
    - Logical operators: AND, OR, NOT
    - Parentheses for grouping
    - Proper operator precedence: () > NOT > AND > OR

    Grammar:
        expression := or_expr
        or_expr := and_expr (OR and_expr)*
        and_expr := not_expr (AND not_expr)*
        not_expr := NOT not_expr | comparison
        comparison := attribute operator value
        attribute := "status_code" | "duration_ms" | "method" | "path" | "user_id" | "duration"
        operator := "==" | "!=" | "<=" | ">=" | "<" | ">" | "not contains" | "contains"
        value := number | quoted_string

    Examples:
        "status_code >= 500"
        "status_code >= 500 AND duration_ms > 1000"
        "(status_code >= 400 AND status_code < 500) OR duration_ms > 2000"
        "method == 'POST' AND (path contains '/api/' OR path contains '/v1/')"
        "NOT status_code == 200"
        "path not contains '/health'"
    """

    # Valid attributes that can be used in CPL expressions
    VALID_ATTRIBUTES = {"status_code", "duration_ms", "duration", "method", "path", "user_id"}

    def __init__(self):
        """Initialize the CPL parser with grammar definition."""
        # Define basic tokens
        integer = pyparsing_common.signed_integer()
        real = pyparsing_common.fnumber
        number = real | integer

        # Attribute names (fields that can be compared)
        identifier = Word(alphas, alphanums + "_")

        # String values (single or double quoted)
        string_value = QuotedString("'", escChar="\\") | QuotedString('"', escChar="\\")

        # Comparison operators - order matters! Check >= before >, <= before <
        comp_op = (
            Literal("==")
            | Literal("!=")
            | Literal("<=")
            | Literal(">=")
            | Literal("<")
            | Literal(">")
        )

        # String contains operators - "not contains" must be checked before "contains"
        contains_op = CaselessKeyword("not") + CaselessKeyword("contains") | CaselessKeyword(
            "contains"
        )

        # Comparison: attribute operator value
        comparison = Group(
            identifier("attribute")
            + (comp_op | contains_op)("operator")
            + (number | string_value)("value")
        )

        # Logical operators with precedence
        # NOT (highest) > AND > OR (lowest)
        expression = infixNotation(
            comparison,
            [
                (CaselessKeyword("NOT"), 1, opAssoc.RIGHT),
                (CaselessKeyword("AND"), 2, opAssoc.LEFT),
                (CaselessKeyword("OR"), 2, opAssoc.LEFT),
            ],
        )

        self.parser = expression
        self.parser = expression
        self._cache = {}  # Cache parsed expressions
        self._cache_lock = threading.Lock()  # Protects _cache

    def parse(self, expression: str):
        """
        Parse CPL expression into parse tree.

        Args:
            expression: CPL expression string

        Returns:
            Parsed expression tree

        Raises:
            ValueError: If expression has invalid syntax
        """
        if not expression or not expression.strip():
            raise ValueError("Expression cannot be empty")

        # Check cache first
        with self._cache_lock:
            if expression in self._cache:
                return self._cache[expression]

        try:
            parsed = self.parser.parseString(expression, parseAll=True)
            with self._cache_lock:
                self._cache[expression] = parsed
            return parsed
        except ParseException as e:
            raise ValueError(
                f"Invalid CPL expression syntax at position {e.loc}: {e.msg}\n"
                f"Expression: {expression}\n"
                f"           {' ' * e.loc}^"
            )

    def evaluate(self, expression: str, attributes: dict) -> bool:
        """
        Evaluate CPL expression against attributes.

        Args:
            expression: CPL expression string
            attributes: Dictionary of attribute values

        Returns:
            True if expression evaluates to true, False otherwise

        Raises:
            ValueError: If expression has invalid syntax or references unknown attributes
        """
        parsed = self.parse(expression)
        return self._eval_tree(parsed[0], attributes)

    def _normalize_token(self, token) -> str:
        """
        Normalize a token from pyparsing (can be string or ParseResults).

        Args:
            token: String or ParseResults from pyparsing

        Returns:
            Normalized lowercase string
        """
        if isinstance(token, str):
            return token.lower()
        # Handle ParseResults from pyparsing
        return "".join(str(x) for x in token).lower()

    def _eval_tree(self, tree, attrs: dict) -> bool:
        """
        Recursively evaluate parsed expression tree from pyparsing's infixNotation.

        Tree structure from pyparsing:
        - Simple comparison: ['attribute', 'operator', value]
        - AND/OR: [left, 'AND'/'OR', right]
        - NOT: ['NOT', operand]

        Note: Operators can be strings or ParseResults due to CaselessKeyword

        Args:
            tree: Parsed expression tree node (list or ParseResults)
            attrs: Attribute values dictionary

        Returns:
            Boolean result of evaluation
        """
        # Convert to list if needed
        if not isinstance(tree, list):
            tree = list(tree)

        # Empty tree
        if not tree:
            return False

        # Simple comparison: ['attribute', 'operator', value] or ['attribute', 'not', 'contains', value]
        if len(tree) == 4 and isinstance(tree[0], str):
            # Check for "not contains" (case-insensitive)
            tok1 = self._normalize_token(tree[1])
            tok2 = self._normalize_token(tree[2])
            if tok1 == "not" and tok2 == "contains":
                return self._eval_comparison_from_list(tree, attrs)
        elif len(tree) == 3 and isinstance(tree[0], str):
            # Check if it's a comparison (not AND/OR/NOT)
            op_str = self._normalize_token(tree[1])
            if op_str not in ("and", "or", "not"):
                # It's a comparison
                return self._eval_comparison_from_list(tree, attrs)

        # Handle NOT operator: ['NOT', operand]
        if len(tree) == 2:
            tok0 = self._normalize_token(tree[0])
            if tok0 == "not":
                return not self._eval_tree(tree[1], attrs)

        # Handle AND/OR operator: [left, 'AND'/'OR', right]
        if len(tree) >= 3:
            # Check if it's an AND or OR operation
            for i, item in enumerate(tree):
                tok = self._normalize_token(item)
                if tok == "and":
                    # Split on all AND operators and evaluate
                    parts = self._split_on_operator(tree, "AND")
                    return all(self._eval_tree(part, attrs) for part in parts)
                elif tok == "or":
                    # Split on all OR operators and evaluate
                    parts = self._split_on_operator(tree, "OR")
                    return any(self._eval_tree(part, attrs) for part in parts)

        # Single element - recurse
        if len(tree) == 1:
            return self._eval_tree(tree[0], attrs)

        return False

    def _split_on_operator(self, tree: list, operator: str) -> list:
        """
        Split tree on given operator (AND/OR), handling both strings and ParseResults.

        Args:
            tree: Tree list
            operator: Operator to split on ('AND' or 'OR')

        Returns:
            List of sub-trees
        """
        parts = []
        current = []
        op_lower = operator.lower()

        for item in tree:
            tok = self._normalize_token(item)
            if tok == op_lower:
                if current:
                    parts.append(current if len(current) > 1 else current[0])
                    current = []
            else:
                current.append(item)

        if current:
            parts.append(current if len(current) > 1 else current[0])

        return parts

    def _eval_comparison_from_list(self, comp_list: list, attrs: dict) -> bool:
        """
        Evaluate a comparison from a list [attribute, operator, value] or [attribute, 'not', 'contains', value].

        Args:
            comp_list: List with [attribute, operator, value] or 4 elements for "not contains"
            attrs: Attribute values dictionary

        Returns:
            Boolean result of comparison
        """
        # Handle "not contains" case: ['path', 'not', 'contains', '/health'] (case-insensitive)
        if (
            len(comp_list) == 4
            and isinstance(comp_list[1], str)
            and comp_list[1].lower() == "not"
            and isinstance(comp_list[2], str)
            and comp_list[2].lower() == "contains"
        ):
            attribute = comp_list[0]
            operator = "not contains"
            value = comp_list[3]
        # Standard case: [attribute, operator, value]
        else:
            attribute = comp_list[0]
            operator = comp_list[1]
            value = comp_list[2]

        # Normalize operator (can be string or list for "not contains")
        if isinstance(operator, list):
            operator = " ".join(str(x) for x in operator)
        operator = str(operator).strip()

        # Normalize and validate attribute (must be lowercase and in valid set)
        attribute_lower = attribute.lower()
        if attribute_lower not in self.VALID_ATTRIBUTES:
            raise ValueError(
                f"Unknown attribute '{attribute}'. "
                f"Valid attributes: {', '.join(sorted(self.VALID_ATTRIBUTES))}"
            )

        # Use normalized attribute name for lookups
        attribute = attribute_lower

        # Get attribute value with backward compatibility fallbacks
        if attribute == "duration_ms":
            # Try duration_ms first, fall back to duration
            attr_value = attrs.get("duration_ms", attrs.get("duration"))
        elif attribute == "duration":
            # Try duration first, fall back to duration_ms
            attr_value = attrs.get("duration", attrs.get("duration_ms"))
        else:
            attr_value = attrs.get(attribute)

        # Handle missing attributes
        if attr_value is None:
            # For numeric comparisons, default to 0
            if attribute in ("status_code", "duration_ms", "duration"):
                attr_value = 0
            # For string comparisons, default to empty string
            else:
                attr_value = ""

        # String operations
        if operator.lower() == "contains":
            return str(value) in str(attr_value)
        elif operator.lower() == "not contains":
            return str(value) not in str(attr_value)

        # Numeric/string comparison operators
        if operator == "==":
            return attr_value == value
        elif operator == "!=":
            return attr_value != value
        elif operator == "<":
            return attr_value < value
        elif operator == "<=":
            return attr_value <= value
        elif operator == ">":
            return attr_value > value
        elif operator == ">=":
            return attr_value >= value

        return False

    def _eval_comparison(self, comp, attrs: dict) -> bool:
        """
        Evaluate a single comparison (deprecated - kept for compatibility).

        Args:
            comp: Parsed comparison node with attribute, operator, value
            attrs: Attribute values dictionary

        Returns:
            Boolean result of comparison

        Raises:
            ValueError: If attribute is unknown
        """
        attribute = comp.attribute
        operator = comp.operator
        value = comp.value

        # Validate attribute
        if attribute not in self.VALID_ATTRIBUTES:
            raise ValueError(
                f"Unknown attribute '{attribute}'. "
                f"Valid attributes: {', '.join(sorted(self.VALID_ATTRIBUTES))}"
            )

        # Get attribute value with backward compatibility fallbacks
        if attribute == "duration_ms":
            # Try duration_ms first, fall back to duration
            attr_value = attrs.get("duration_ms", attrs.get("duration"))
        elif attribute == "duration":
            # Try duration first, fall back to duration_ms
            attr_value = attrs.get("duration", attrs.get("duration_ms"))
        else:
            attr_value = attrs.get(attribute)

        # Handle missing attributes
        if attr_value is None:
            # For numeric comparisons, default to 0
            if attribute in ("status_code", "duration_ms", "duration"):
                attr_value = 0
            # For string comparisons, default to empty string
            else:
                attr_value = ""

        # Normalize operator (can be string or list)
        if isinstance(operator, list):
            operator = " ".join(str(x) for x in operator)
        operator = str(operator).strip()

        # String operations
        if operator.lower() == "contains":
            return str(value) in str(attr_value)
        elif operator.lower() == "not contains":
            return str(value) not in str(attr_value)

        # Numeric/string comparison operators
        if operator == "==":
            return attr_value == value
        elif operator == "!=":
            return attr_value != value
        elif operator == "<":
            return attr_value < value
        elif operator == "<=":
            return attr_value <= value
        elif operator == ">":
            return attr_value > value
        elif operator == ">=":
            return attr_value >= value

        return False


class CPLCondition:
    """
    Wrapper for CPL condition with evaluate() method.
    Uses the complete CPLParser for expression evaluation.
    """

    # Shared parser instance for all conditions (cached expressions)
    _parser = None

    def __init__(self, condition_dict: dict):
        self.name = condition_dict.get("name", "unnamed")
        self.when = condition_dict.get("when", "")
        self.enabled = condition_dict.get("enabled", True)
        self._condition = condition_dict

        # Initialize shared parser on first use
        if CPLCondition._parser is None:
            CPLCondition._parser = CPLParser()

    def evaluate(self, attrs: dict) -> bool:
        """
        Evaluate CPL condition against span attributes.

        Uses the complete CPL expression parser supporting:
        - All comparison operators: ==, !=, <, <=, >, >=
        - String operators: contains, not contains
        - Logical operators: AND, OR, NOT
        - Parentheses for grouping

        Args:
            attrs: Span attributes dictionary

        Returns:
            True if condition matches, False otherwise

        Examples:
            "status_code >= 500"
            "status_code >= 500 AND duration_ms > 1000"
            "(status_code >= 400 AND status_code < 500) OR duration_ms > 2000"
            "method == 'POST' AND path contains '/api/'"
            "NOT status_code == 200"
        """
        import logging

        logger = logging.getLogger(__name__)

        # Skip disabled conditions
        if not self.enabled:
            logger.debug(f"  Condition '{self.name}': disabled, skipping")
            return False

        # Skip empty expressions
        if not self.when or not self.when.strip():
            logger.debug(f"  Condition '{self.name}': empty expression, skipping")
            return False

        try:
            # Evaluate using the new parser
            result = CPLCondition._parser.evaluate(self.when, attrs)
            logger.debug(f"  Condition '{self.name}': {self.when} => {result}")
            return result
        except ValueError as e:
            # Log parse/evaluation errors but don't crash
            logger.error(f"  Condition '{self.name}': Error evaluating '{self.when}': {e}")
            return False
        except Exception as e:
            # Catch any unexpected errors
            logger.error(f"  Condition '{self.name}': Unexpected error: {e}")
            return False


@dataclass
class GovernanceDecision:
    """Result of governance evaluation"""

    should_sample: bool
    reason: str
    rule_name: Optional[str] = None
    sampling_rate: Optional[float] = None
    policy_version: Optional[str] = None
    should_record_logs: bool = True
    matched_conditions: list = field(default_factory=list)
    final_rate: float = 0.0


class ObservabilityAdapter(ABC):
    """
    Universal interface that ANY observability tool adapter must implement.

    This is the contract between Clarvynn's core governance engine
    and specific observability tool implementations.
    """

    def __init__(self, cpl_policy: Optional[Dict[str, Any]] = None):
        self.cpl_policy = cpl_policy or {}
        self.stats = {"total_requests": 0, "sampled": 0, "dropped": 0, "errors": 0}

    @abstractmethod
    def setup(self) -> bool:
        """
        Initialize the adapter with the observability tool.
        Returns True if setup successful, False otherwise.
        """
        pass

    @abstractmethod
    def apply_governance(self, request_data: RequestData) -> GovernanceDecision:
        """
        Apply Clarvynn governance to a request.
        This is where CPL evaluation happens.
        """
        pass

    @abstractmethod
    def export_telemetry(self, request_data: RequestData, decision: GovernanceDecision) -> bool:
        """
        Export telemetry data if governance decision says to keep it.
        Implementation varies by observability tool.
        """
        pass

    @abstractmethod
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get current governance metrics (sampled, dropped, rates, etc.)
        """
        pass

    @abstractmethod
    def get_adapter_info(self) -> Dict[str, str]:
        """
        Return information about this adapter.
        Example: {"type": "opentelemetry", "version": "1.32.0", "status": "active"}
        """
        pass

    def shutdown(self):
        """Cleanup resources when shutting down"""
        pass
