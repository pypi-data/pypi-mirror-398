"""
Business Rules Engine - Declarative Validation

Complex, declarative constraint validation beyond basic field validation.
"""

from functools import wraps


class Rule:
    """Represents a business rule"""

    def __init__(self, name, func, priority=0, message=None):
        self.name = name
        self.func = func
        self.priority = priority
        self.message = message or f"Rule '{name}' failed"

    def validate(self, instance):
        """Run the rule validation"""
        try:
            result = self.func(instance)
            if not result:
                return False, self.message
            return True, None
        except Exception as e:
            return False, f"{self.message}: {str(e)}"


class RuleViolation(Exception):
    """Raised when a business rule is violated"""

    pass


class RuleEngine:
    """Manages and executes business rules"""

    def __init__(self):
        self.rules = {}  # model_class -> [Rule, ...]

    def register(self, model_class, rule):
        """Register a rule for a model"""
        if model_class not in self.rules:
            self.rules[model_class] = []
        self.rules[model_class].append(rule)
        # Sort by priority (higher first)
        self.rules[model_class].sort(key=lambda r: r.priority, reverse=True)

    def validate(self, instance):
        """Validate instance against all rules"""
        model_class = instance.__class__
        if model_class not in self.rules:
            return True, []

        violations = []
        for rule in self.rules[model_class]:
            valid, message = rule.validate(instance)
            if not valid:
                violations.append(message)

        return len(violations) == 0, violations


# Global rule engine
_rule_engine = RuleEngine()


def get_rule_engine():
    return _rule_engine


def rule(name, priority=0, message=None):
    """
    Decorator to define a business rule.

    Usage:
        @User.rule("age_validation", priority=10)
        def validate_age(user):
            return user.age >= 18
    """

    def decorator(func):
        # This returns a decorator that will be used on the model
        def model_decorator(model_class):
            r = Rule(name, func, priority, message)
            get_rule_engine().register(model_class, r)
            return model_class

        # Store the decorator for later use
        func._rule_name = name
        func._rule_priority = priority
        func._rule_message = message
        return func

    return decorator


def add_rules_to_model():
    """Add business rules to Model"""
    from .model import Model

    # Add rule decorator as class method
    @classmethod
    def add_rule(cls, name, priority=0, message=None):
        """Decorator to add a rule to this model"""

        def decorator(func):
            r = Rule(name, func, priority, message)
            get_rule_engine().register(cls, r)

            # Attach to class for reference
            if not hasattr(cls, "_business_rules"):
                cls._business_rules = []
            cls._business_rules.append(r)

            return func

        return decorator

    Model.rule = add_rule

    # Patch validate to include business rules
    original_validate = Model.validate

    def validate_with_rules(self):
        # Run normal validation
        original_validate(self)

        # Run business rules
        valid, violations = get_rule_engine().validate(self)
        if not valid:
            raise RuleViolation(f"Business rule violations: {', '.join(violations)}")

    Model.validate = validate_with_rules

    # Add helper to check rules without raising
    def check_rules(self):
        """Check business rules without raising exception"""
        return get_rule_engine().validate(self)

    Model.check_rules = check_rules
